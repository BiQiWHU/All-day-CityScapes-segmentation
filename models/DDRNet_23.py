import math
import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import init
from collections import OrderedDict

BatchNorm2d = nn.BatchNorm2d
bn_mom = 0.1


def conv3x3(in_planes, out_planes, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride,
                     padding=1, bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None, no_relu=False):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = BatchNorm2d(planes, momentum=bn_mom)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = BatchNorm2d(planes, momentum=bn_mom)
        self.downsample = downsample
        self.stride = stride
        self.no_relu = no_relu

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual

        if self.no_relu:
            return out
        else:
            return self.relu(out)


class Bottleneck(nn.Module):
    expansion = 2

    def __init__(self, inplanes, planes, stride=1, downsample=None, no_relu=True):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = BatchNorm2d(planes, momentum=bn_mom)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride,
                               padding=1, bias=False)
        self.bn2 = BatchNorm2d(planes, momentum=bn_mom)
        self.conv3 = nn.Conv2d(planes, planes * self.expansion, kernel_size=1,
                               bias=False)
        self.bn3 = BatchNorm2d(planes * self.expansion, momentum=bn_mom)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride
        self.no_relu = no_relu

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        if self.no_relu:
            return out
        else:
            return self.relu(out)


class DAPPM(nn.Module):
    def __init__(self, inplanes, branch_planes, outplanes):
        super(DAPPM, self).__init__()
        self.scale1 = nn.Sequential(nn.AvgPool2d(kernel_size=5, stride=2, padding=2),
                                    BatchNorm2d(inplanes, momentum=bn_mom),
                                    nn.ReLU(inplace=True),
                                    nn.Conv2d(inplanes, branch_planes,
                                              kernel_size=1, bias=False),
                                    )
        self.scale2 = nn.Sequential(nn.AvgPool2d(kernel_size=9, stride=4, padding=4),
                                    BatchNorm2d(inplanes, momentum=bn_mom),
                                    nn.ReLU(inplace=True),
                                    nn.Conv2d(inplanes, branch_planes,
                                              kernel_size=1, bias=False),
                                    )
        self.scale3 = nn.Sequential(nn.AvgPool2d(kernel_size=17, stride=8, padding=8),
                                    BatchNorm2d(inplanes, momentum=bn_mom),
                                    nn.ReLU(inplace=True),
                                    nn.Conv2d(inplanes, branch_planes,
                                              kernel_size=1, bias=False),
                                    )
        self.scale4 = nn.Sequential(nn.AdaptiveAvgPool2d((1, 1)),
                                    BatchNorm2d(inplanes, momentum=bn_mom),
                                    nn.ReLU(inplace=True),
                                    nn.Conv2d(inplanes, branch_planes,
                                              kernel_size=1, bias=False),
                                    )
        self.scale0 = nn.Sequential(
            BatchNorm2d(inplanes, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(inplanes, branch_planes, kernel_size=1, bias=False),
        )
        self.process1 = nn.Sequential(
            BatchNorm2d(branch_planes, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(branch_planes, branch_planes,
                      kernel_size=3, padding=1, bias=False),
        )
        self.process2 = nn.Sequential(
            BatchNorm2d(branch_planes, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(branch_planes, branch_planes,
                      kernel_size=3, padding=1, bias=False),
        )
        self.process3 = nn.Sequential(
            BatchNorm2d(branch_planes, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(branch_planes, branch_planes,
                      kernel_size=3, padding=1, bias=False),
        )
        self.process4 = nn.Sequential(
            BatchNorm2d(branch_planes, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(branch_planes, branch_planes,
                      kernel_size=3, padding=1, bias=False),
        )
        self.compression = nn.Sequential(
            BatchNorm2d(branch_planes * 5, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(branch_planes * 5, outplanes, kernel_size=1, bias=False),
        )
        self.shortcut = nn.Sequential(
            BatchNorm2d(inplanes, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(inplanes, outplanes, kernel_size=1, bias=False),
        )

    def forward(self, x):

        # x = self.downsample(x)
        width = x.shape[-1]
        height = x.shape[-2]
        x_list = []

        x_list.append(self.scale0(x))
        x_list.append(self.process1((F.interpolate(self.scale1(x),
                                                   size=[height, width],
                                                   mode='bilinear')+x_list[0])))
        x_list.append((self.process2((F.interpolate(self.scale2(x),
                                                    size=[height, width],
                                                    mode='bilinear')+x_list[1]))))
        x_list.append(self.process3((F.interpolate(self.scale3(x),
                                                   size=[height, width],
                                                   mode='bilinear')+x_list[2])))
        x_list.append(self.process4((F.interpolate(self.scale4(x),
                                                   size=[height, width],
                                                   mode='bilinear')+x_list[3])))

        out = self.compression(torch.cat(x_list, 1)) + self.shortcut(x)
        return out


class segmenthead(nn.Module):

    def __init__(self, inplanes, interplanes, outplanes, scale_factor=None):
        super(segmenthead, self).__init__()
        self.bn1 = BatchNorm2d(inplanes, momentum=bn_mom)
        self.conv1 = nn.Conv2d(inplanes, interplanes,
                               kernel_size=3, padding=1, bias=False)
        self.bn2 = BatchNorm2d(interplanes, momentum=bn_mom)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(interplanes, outplanes,
                               kernel_size=1, padding=0, bias=True)
        self.scale_factor = scale_factor
        
        ### for C representation branch. feature refine and attention weight matrix
        self.conv3 = nn.Sequential(
            nn.Conv2d(256, 1, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(1, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        ### for A representation branch. feature refine and attention weight matrix
        self.conv4 = nn.Sequential(
            nn.Conv2d(256, 1, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(1, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        self.conv5 = nn.Sequential(
            nn.Conv2d(256, 19, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(19, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        self.conv6 = nn.Sequential(
            nn.Conv2d(256, 19, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(19, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )

    def forward(self, C, A):
        
        attention_c=self.conv3(C)
        attention_a=self.conv4(A)
        
        C_ = 2*C + attention_c *C + A *attention_c
        A_ =A + attention_a *A

        x = self.conv1(self.relu(self.bn1(C_+A_)))
        out = self.conv2(self.relu(self.bn2(x)))
        
        Cupdate=self.conv5(C)
        C_update=self.conv6(C_)

        if self.scale_factor is not None:
            height = x.shape[-2] * self.scale_factor
            width = x.shape[-1] * self.scale_factor
            out = F.interpolate(out,
                                size=[height, width],
                                mode='bilinear')

        return out, C_update, Cupdate


class segmentheadold(nn.Module):

    def __init__(self, inplanes, interplanes, outplanes, scale_factor=None):
        super(segmenthead, self).__init__()
        self.bn1 = BatchNorm2d(inplanes, momentum=bn_mom)
        self.conv1 = nn.Conv2d(inplanes, interplanes,
                               kernel_size=3, padding=1, bias=False)
        self.bn2 = BatchNorm2d(interplanes, momentum=bn_mom)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(interplanes, outplanes,
                               kernel_size=1, padding=0, bias=True)
        self.scale_factor = scale_factor

    def forward(self, x):

        x = self.conv1(self.relu(self.bn1(x)))
        out = self.conv2(self.relu(self.bn2(x)))

        if self.scale_factor is not None:
            height = x.shape[-2] * self.scale_factor
            width = x.shape[-1] * self.scale_factor
            out = F.interpolate(out,
                                size=[height, width],
                                mode='bilinear')

        return out


class DualResNet(nn.Module):

    def __init__(self, block, layers, num_classes=19, planes=64, spp_planes=128, head_planes=128, augment=False):
        super(DualResNet, self).__init__()

        highres_planes = planes * 2
        self.augment = augment

        self.conv1 = nn.Sequential(
            nn.Conv2d(3, planes, kernel_size=3, stride=2, padding=1),
            BatchNorm2d(planes, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(planes, planes, kernel_size=3, stride=2, padding=1),
            BatchNorm2d(planes, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )

        self.relu = nn.ReLU(inplace=False)
        self.layer1 = self._make_layer(block, planes, planes, layers[0])
        self.layer2 = self._make_layer(
            block, planes, planes * 2, layers[1], stride=2)
        self.layer3 = self._make_layer(
            block, planes * 2, planes * 4, layers[2], stride=2)
        self.layer4 = self._make_layer(
            block, planes * 4, planes * 8, layers[3], stride=2)

        self.compression3 = nn.Sequential(
            nn.Conv2d(planes * 4, highres_planes, kernel_size=1, bias=False),
            BatchNorm2d(highres_planes, momentum=bn_mom),
        )

        self.compression4 = nn.Sequential(
            nn.Conv2d(planes * 8, highres_planes, kernel_size=1, bias=False),
            BatchNorm2d(highres_planes, momentum=bn_mom),
        )

        self.down3 = nn.Sequential(
            nn.Conv2d(highres_planes, planes * 4, kernel_size=3,
                      stride=2, padding=1, bias=False),
            BatchNorm2d(planes * 4, momentum=bn_mom),
        )

        self.down4 = nn.Sequential(
            nn.Conv2d(highres_planes, planes * 4, kernel_size=3,
                      stride=2, padding=1, bias=False),
            BatchNorm2d(planes * 4, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(planes * 4, planes * 8, kernel_size=3,
                      stride=2, padding=1, bias=False),
            BatchNorm2d(planes * 8, momentum=bn_mom),
        )

        self.layer3_ = self._make_layer(block, planes * 2, highres_planes, 2)

        self.layer4_ = self._make_layer(
            block, highres_planes, highres_planes, 2)

        self.layer5_ = self._make_layer(
            Bottleneck, highres_planes, highres_planes, 1)

        self.layer5 = self._make_layer(
            Bottleneck, planes * 8, planes * 8, 1, stride=2)

        self.spp = DAPPM(planes * 16, spp_planes, planes * 4)

        if self.augment:
            self.seghead_extra = segmenthead(
                highres_planes, head_planes, num_classes)

        self.final_layer = segmenthead(planes * 4, head_planes, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(
                    m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def _make_layer(self, block, inplanes, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion, momentum=bn_mom),
            )

        layers = []
        layers.append(block(inplanes, planes, stride, downsample))
        inplanes = planes * block.expansion
        for i in range(1, blocks):
            if i == (blocks-1):
                layers.append(block(inplanes, planes, stride=1, no_relu=True))
            else:
                layers.append(block(inplanes, planes, stride=1, no_relu=False))

        return nn.Sequential(*layers)

    def forward(self, x):

        width_output_or = x.shape[-1]
        height_output_or = x.shape[-2]

        width_output = x.shape[-1] // 8
        height_output = x.shape[-2] // 8
        layers = []

        x = self.conv1(x)

        x = self.layer1(x)
        layers.append(x)

        x = self.layer2(self.relu(x))
        layers.append(x)

        x = self.layer3(self.relu(x))
        layers.append(x)
        
        x_ = self.layer3_(self.relu(layers[1]))  #### [4,128,128,128]

        x = x + self.down3(self.relu(x_)) ###[4,256,64,64]
        
        x_ = x_ + F.interpolate(
            self.compression3(self.relu(layers[2])),
            size=[height_output, width_output],
            mode='bilinear')   ###[4,128,64,64]
        
        if self.augment:
            temp = x_

        x = self.layer4(self.relu(x))
        layers.append(x)
        x_ = self.layer4_(self.relu(x_))

        x = x + self.down4(self.relu(x_))
        x_ = x_ + F.interpolate(
            self.compression4(self.relu(layers[3])),
            size=[height_output, width_output],
            mode='bilinear')   ###[4,128,128,128]

        ### high-resolution 1/8  apperance branch     
        before_E = x_
        x_ = self.layer5_(self.relu(x_))
        x_a = x_   ###[4,256,128,128]
        after_E = x_
        
         ### low resolution 1/64 branch, need upsampling, content branch
        x = self.layer5(self.relu(x))
        before_I = F.interpolate(
            x,
            size=[height_output, width_output],
            mode='bilinear')
        x = F.interpolate(
            self.spp(x),
            size=[height_output, width_output],
            mode='bilinear')
        x_c = x   ###[4,256,128,128]
        after_I = x

        x_, C, C_ = self.final_layer(x, x_)  ### seghead [4,19,128,128]

        outputs = []

        x_ = F.interpolate(x_,
                           size=[height_output_or, width_output_or],
                           mode='bilinear', align_corners=True)   #[4,19,1024,1024]
        
        outputs.append(x_)

        if self.augment:
            x_extra = self.seghead_extra(temp)
            return [x_, x_extra]
        else:
            return tuple(outputs), C_, C 


def DualResNet_imagenet(pretrained=True):
    model = DualResNet(BasicBlock, [2, 2, 2, 2], num_classes=19,
                       planes=64, spp_planes=128, head_planes=128, augment=False)
    if pretrained:
        pretrained_state = torch.load(
            "D:/DDR/models/DDRNet23_imagenet.pth", map_location='cpu')
        model_dict = model.state_dict()
        pretrained_state = {k: v for k, v in pretrained_state.items() if
                            (k in model_dict and v.shape == model_dict[k].shape)}
        model_dict.update(pretrained_state)

        model.load_state_dict(model_dict, strict=False)
        print("Having loaded imagenet-pretrained weights successfully!")

    return model


def get_ddrnet_23(pretrained=True):

    model = DualResNet_imagenet(pretrained=pretrained)
    return model


### C-leaner & A-learner later part

class CAinteract(nn.Module):

    def __init__(self, num_classes=19, planes=64, spp_planes=128, head_planes=128, augment=False):
        super(CAinteract, self).__init__()

        self.augment = augment
        highres_planes = planes * 2
        
        ### for C representation branch. feature refine and attention weight matrix
        self.conv1 = nn.Sequential(
            nn.Conv2d(256, 256, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(256, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 1, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(1, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        ### for A representation branch. feature refine and attention weight matrix
        self.conv2 = nn.Sequential(
            nn.Conv2d(256, 256, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(256, momentum=bn_mom),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 1, kernel_size=1, stride=1, padding=0),
            BatchNorm2d(1, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        self.relu = nn.ReLU(inplace=False)
        
        if self.augment:
            self.seghead_extra = segmenthead(
                highres_planes, head_planes, num_classes)

        self.final_layer = segmenthead(planes * 4, head_planes, num_classes)
        

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(
                    m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def _make_layer(self, block, inplanes, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion, momentum=bn_mom),
            )

        layers = []
        layers.append(block(inplanes, planes, stride, downsample))
        inplanes = planes * block.expansion
        for i in range(1, blocks):
            if i == (blocks-1):
                layers.append(block(inplanes, planes, stride=1, no_relu=True))
            else:
                layers.append(block(inplanes, planes, stride=1, no_relu=False))

        return nn.Sequential(*layers)

    def forward(self, X_, C, A):

        # layers = []
        height_output=1024
        width_output=1024

        attention_c = self.conv1(C)
        attention_a = self.conv2(A)

        C=C*attention_c+C
        A=A*attention_a+A
        
        x_ = self.final_layer(2*X_+ C + A)  ### seghead [4,19,128,128]

        outputs = []

        x_ = F.interpolate(x_,
                           size=[height_output, width_output],
                           mode='bilinear', align_corners=True)   #[4,19,1024,1024]
        
        outputs.append(x_)

        return tuple(outputs), C, A


### C-A merge module

class CAmerge(nn.Module):

    def __init__(self, planes=64, augment=False):
        super(CAmerge, self).__init__()

        highres_planes = planes * 2
        self.augment = augment
        
        #### for upsample 1/8 to 1/4   256->64

        self.conv1 = nn.Sequential(
            # nn.Conv2d(256, 128, kernel_size=1, stride=1, padding=1),
            # BatchNorm2d(128, momentum=bn_mom),
            # nn.ReLU(inplace=True),
            nn.Conv2d(256, planes, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(planes, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        ##### for upsample 1/4 to 1/2  64->32
        self.conv2 = nn.Sequential(
            nn.Conv2d(planes, 32, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(32, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        ##### for upsample 1/2 to orginal 1/1  32->3
        self.conv3 = nn.Sequential(
            nn.Conv2d(32, 3, kernel_size=3, stride=1, padding=1),
            BatchNorm2d(3, momentum=bn_mom),
            nn.ReLU(inplace=True),
        )
        
        self.relu = nn.ReLU(inplace=False)

        # if self.augment:
        #     self.seghead_extra = segmenthead(
        #         highres_planes, head_planes, num_classes)

        # self.final_layer = segmenthead(planes * 4, head_planes, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(
                    m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, C, A):

        layers = []

        ### C and A are from 1/8 resolution, input for reconstruction   ###[4,256,128,128] -> [4,64,128,128] -> [4,64,256,256]
        x = self.conv1(C+A)  
        layers.append(x)
        ## upsample 128->256
        x = F.interpolate(
            self.relu(layers[0]),
            size=[256,256],
            mode='bilinear')

        ###[4,64,256,256] -> [4,32,256,256] -> [4,32,512,512]
        x = self.conv2(self.relu(x))     
        # if x_41 has more channels than 64 (plane), then first need to add another layer to compress it to 64 channels
        layers.append(x)
        ## upsample 256->512
        x = F.interpolate(
            self.relu(layers[1]),
            size=[512,512],
            mode='bilinear')
        
        ###[4,32,512,512] -> [4,3,512,512] -> [4,3,1024,1024]

        x = self.conv3(self.relu(x))
        layers.append(x)
        
        x = F.interpolate(
            self.relu(layers[2]),
            size=[1024, 1024],
            mode='bilinear')   ###[4,128,64,64]
        
        if self.augment:
            temp = x

        outputs = []
        
        outputs.append(x)

        if self.augment:
            x_extra = self.seghead_extra(temp)
            return [x, x_extra]
        else:
            return tuple(outputs), x

def get_CA_interact( ):
    model = CAinteract( )
    return model

def get_CA_merge( ):
    model = CAmerge( )
    return model

if __name__ == "__main__":

    model = DualResNet_imagenet(pretrained=True)
