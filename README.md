# All-day-CityScapes-segmentation
All-day Semantic Segmentation &amp; All-day CityScapes dataset

This is the official implementation of our work entitled as ```Interactive Learning of Intrinsic and Extrinsic Properties for All-day Semantic Segmentation```, accepted by ```IEEE Transactions on Image Processing```.

![avatar](/heatmapAD.png)

# Dataset Download

Please click <a href="isis-data.science.uva.nl/cv/1ADcityscape.zip"> here</a> to download ```All-day CityScapes```.

For CopyRight issue, we only provide the rendered samples on both training and validation set of the original ```CityScapes```.

All the sample name and data folder organization from ```All-day CityScapes``` is the same as the original ```CityScapes```.

# Source Code & Implementation

The proposed ```interactive intrinsic-extrinsic learning``` can be embedded into a variety of ```CNN``` and ```ViT``` based segmentation models.

Here we provide the source code that is implemented on <a href="https://ieeexplore.ieee.org/document/9996293">DDRNet-23</a> backbone, which is: 1) simple and easy to config; 2) most of the experiments in this paper conduct on. 
This implementation is highly based on the DDRNet source code. The original implementation of DDRNet can be found in this <a href="https://github.com/ydhongHIT/DDRNet">page</a>.

Please follow the below steps to run the AO-SegNet (DDRNet-23 based).

Step 1: Configuration

# Citation and Reference
If you find this project useful, please cite:
```
@ARTICLE{Bi2023AD,
  author={Bi, Qi and You, Shaodi and Gevers, Theo},
  journal={IEEE Transactions on Image Processing}, 
  title={Interactive Learning of Intrinsic and Extrinsic Properties for All-day Semantic Segmentation}, 
  year={2023},
  volume={32},
  number={},
  pages={3821-3835},
  doi={10.1109/TIP.2023.3290469}}
```
