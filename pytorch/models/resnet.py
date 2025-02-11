import torch.nn as nn
import torch.nn.functional as F

# list of public names that should be imported when this module is imported 
__all__ = ["ResNet18", "ResNet34", "ResNet50", "ResNet101", "ResNet152"]


class BasicBlock(nn.Module):
    # expansion factor for the number of channels in the output feature maps (depth)
    expansion = 1

    def __init__(self, in_planes, planes, layer_config):
        # layerconfig : dictionary containing configuration parameters for the layers within the block

        super(BasicBlock, self).__init__()
        conv = layer_config["conv"]
        stride = layer_config["stride"]
        self.conv1 = conv(
            in_planes,
            planes,
            kernel_size=3,
            stride=stride,
            padding=1,
            bias=False,
            args=layer_config,
        )
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = conv(
            planes,
            planes,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False,
            args=layer_config,
        )
        self.bn2 = nn.BatchNorm2d(planes)

        self.shortcut = nn.Sequential()
        # A "shortcut" connection is created. 
        # If the stride of the block is not 1 (it downsamples the input) 
        # or if the number of input channels does not match the number of output channels after expansion, 
        # we apply conv1x1 is to match the dimensions
        if stride != 1 or in_planes != self.expansion * planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(
                    in_planes,
                    self.expansion * planes,
                    kernel_size=1,
                    stride=stride,
                    bias=False,
                ),
                nn.BatchNorm2d(self.expansion * planes),
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        # skip connection
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, in_planes, planes, stride=1):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(
            planes, planes, kernel_size=3, stride=stride, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(
            planes, self.expansion * planes, kernel_size=1, bias=False
        )
        self.bn3 = nn.BatchNorm2d(self.expansion * planes)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != self.expansion * planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(
                    in_planes,
                    self.expansion * planes,
                    kernel_size=1,
                    stride=stride,
                    bias=False,
                ),
                nn.BatchNorm2d(self.expansion * planes),
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = F.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class ResNet(nn.Module):
    def __init__(self, block, num_blocks, configs=None, num_classes=10):
        super(ResNet, self).__init__()
        self.configs = configs
        self.in_planes = 64

        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.layer1 = self._make_layer(
            block, 64, num_blocks[0], configs[0]
        )  # , stride=1)
        self.layer2 = self._make_layer(
            block, 128, num_blocks[1], configs[1]
        )  # , stride=2)
        self.layer3 = self._make_layer(
            block, 256, num_blocks[2], configs[2]
        )  # , stride=2)
        self.layer4 = self._make_layer(
            block, 512, num_blocks[3], configs[3]
        )  # , stride=2)
        self.linear = nn.Linear(512 * block.expansion, num_classes)

    def _make_layer(self, block, planes, num_blocks, configs):
        # strides = [stride] + [1]*(num_blocks-1)
        layers = []
        for layer_config in configs:
            layers.append(block(self.in_planes, planes, layer_config))
            self.in_planes = planes * block.expansion
        return nn.Sequential(*layers)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = F.avg_pool2d(out, 4)
        out = out.view(out.size(0), -1)
        out = self.linear(out)
        return out


def ResNet18(configs):
    return ResNet(BasicBlock, [2, 2, 2, 2], configs)


def ResNet34(configs):
    return ResNet(BasicBlock, [3, 4, 6, 3], configs)


def ResNet50(configs):
    return ResNet(Bottleneck, [3, 4, 6, 3], configs)


def ResNet101(configs):
    return ResNet(Bottleneck, [3, 4, 23, 3], configs)


def ResNet152(configs):
    return ResNet(Bottleneck, [3, 8, 36, 3], configs)
