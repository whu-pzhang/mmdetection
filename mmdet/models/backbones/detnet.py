import math

import torch.nn as nn

from mmdet.ops import (build_conv_layer, build_norm_layer)
from ..registry import BACKBONES


def conv3x3(in_planes, out_planes, stride=1):
    "3x3 convolution with padding"
    return nn.Conv2d(
        in_planes,
        out_planes,
        kernel_size=3,
        stride=stride,
        padding=1,
        bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

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
        out = self.relu(out)

        return out


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(
            planes,
            planes,
            kernel_size=3,
            stride=stride,
            padding=1,
            bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

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
        out = self.relu(out)

        return out


class BottleneckA(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BottleneckA, self).__init__()
        assert inplanes == (planes * 4), 'inplanes != planes * 4'
        assert stride == 1, 'stride != 1'
        assert downsample is None, 'downsample is not None'
        self.conv1 = nn.Conv2d(
            inplanes, planes, kernel_size=1,
            bias=False)  # inplanes = 1024, planes = 256
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(
            planes,
            planes,
            kernel_size=3,
            stride=1,
            dilation=2,
            padding=2,
            bias=False)  # stride = 1, dilation = 2
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride

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

        if self.downsample is not None:  # downsample always is None, because stride=1 and inplanes=expansion * planes
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class BottleneckB(nn.Module):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BottleneckB, self).__init__()
        assert inplanes == (planes * 4), 'inplanes != planes * 4'
        assert stride == 1, 'stride != 1'
        assert downsample is None, 'downsample is not None'
        self.conv1 = nn.Conv2d(
            inplanes, planes, kernel_size=1,
            bias=False)  # inplanes = 1024, planes = 256
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(
            planes,
            planes,
            kernel_size=3,
            stride=1,
            dilation=2,
            padding=2,
            bias=False)  # stride = 1, dilation = 2
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride
        self.extra_conv = nn.Sequential(
            nn.Conv2d(inplanes, planes * 4, kernel_size=1, bias=False),
            nn.BatchNorm2d(planes * 4))

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        residual = self.extra_conv(x)

        if self.downsample is not None:  # downsample always is None, because stride=1 and inplanes=expansion * planes
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


@BACKBONES.register_module
class DetNet(nn.Module):

    arch_settings = {
        59: (Bottleneck, (3, 4, 6, 3, 3)),
        101: (Bottleneck, (3, 4, 23, 3, 3)),
    }

    def __init__(
            self,
            depth,
            in_channels=3,
            num_stages=5,
            strides=(1, 2, 2, 1, 1),
            dilations=(1, 1, 1, 2, 2),
            out_indices=(0, 1, 2, 3, 4),
    ):
        self.inplanes = 64
        super(DetNet, self).__init__()
        if depth not in self.arch_settings:
            raise KeyError('invalid depth {} for resnet'.format(depth))
        self.depth = depth
        self.num_stages = num_stages
        assert num_stages >= 1 and num_stages <= 5

        self.block, stage_blocks = self.arch_settings[depth]

        self.conv1 = nn.Conv2d(
            3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(self.block, 64, stage_blocks[0])
        self.layer2 = self._make_layer(
            self.block, 128, stage_blocks[1], stride=2)
        self.layer3 = self._make_layer(
            self.block, 256, stage_blocks[2], stride=2)
        self.layer4 = self._make_new_layer(256, stage_blocks[3])
        self.layer5 = self._make_new_layer(256, stage_blocks[4])

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(
                    self.inplanes,
                    planes * block.expansion,
                    kernel_size=1,
                    stride=stride,
                    bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def _make_new_layer(self, planes, blocks):
        downsample = None
        block_b = BottleneckB
        block_a = BottleneckA

        layers = []
        layers.append(
            block_b(self.inplanes, planes, stride=1, downsample=downsample))
        self.inplanes = planes * block_b.expansion
        for i in range(1, blocks):
            layers.append(block_a(self.inplanes, planes))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.layer5(x)

        return x
