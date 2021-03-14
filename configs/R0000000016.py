import copy
from inspect import getmembers, isfunction
from threading import Lock
import os

import numpy as np
import torch
import torchvision
import torch.nn.functional as F
from torchvision import transforms
from torch import nn

lock = Lock()


class Dataloader(object):
    def __init__(self, path, batch_size):
        self.path = path
        self.batch_size = batch_size

    def traindataloader(self):
        train_transform = transforms.Compose([
            transforms.RandomCrop(32, padding=4),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])
        train_dataset = torchvision.datasets.ImageFolder(
            root=os.path.join(self.path, 'train'),
            transform=train_transform)
        return torch.utils.data.DataLoader(
            train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=2)

    def testdataloader(self):
        test_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ])
        test_dataset = torchvision.datasets.ImageFolder(
            root=os.path.join(self.path, 'test'),
            transform=test_transform)
        return torch.utils.data.DataLoader(
            test_dataset, batch_size=self.batch_size, shuffle=True, num_workers=2)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, in_planes, planes, stride=1):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(
            in_planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3,
                               stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != self.expansion * planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_planes, self.expansion * planes,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(self.expansion * planes)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, in_planes, planes, stride=1):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3,
                               stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, self.expansion *
                               planes, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(self.expansion * planes)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != self.expansion * planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_planes, self.expansion * planes,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(self.expansion * planes)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = F.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class ResNet(nn.Module):
    def __init__(self, block, num_blocks, num_classes=10):
        super(ResNet, self).__init__()
        self.in_planes = 64

        self.conv1 = nn.Conv2d(3, 64, kernel_size=3,
                               stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.layer1 = self._make_layer(block, 64, num_blocks[0], stride=1)
        self.layer2 = self._make_layer(block, 128, num_blocks[1], stride=2)
        self.layer3 = self._make_layer(block, 256, num_blocks[2], stride=2)
        self.layer4 = self._make_layer(block, 512, num_blocks[3], stride=2)
        self.linear = nn.Linear(512 * block.expansion, num_classes)

    def _make_layer(self, block, planes, num_blocks, stride):
        strides = [stride] + [1] * (num_blocks - 1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride))
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


def ResNet18():
    return ResNet(BasicBlock, [2, 2, 2, 2])


def ResNet34():
    return ResNet(BasicBlock, [3, 4, 6, 3])


def ResNet50():
    return ResNet(Bottleneck, [3, 4, 6, 3])


def ResNet101():
    return ResNet(Bottleneck, [3, 4, 23, 3])


def ResNet152():
    return ResNet(Bottleneck, [3, 8, 36, 3])


def DeepNet():
    net = ResNet18()
    return net


def loss(output, target):
    return nn.CrossEntropyLoss()(output, target)


class Metric(object):
    @staticmethod
    def accuracy(output, target):
        with torch.no_grad():
            pred = torch.argmax(output, dim=1)
            assert pred.shape[0] == len(target)
            correct = torch.sum(pred == target).item()
        return correct


class ExtractorEvaluator(object):
    def __init__(self, reg_val, batchsize, ckp_path, data_path, roomid):
        self.best = 0
        self.reg_val = reg_val
        self.batch_size = batchsize
        self.ckp_path = ckp_path
        self.data_path = data_path
        self.roomid = roomid

        self.train_dataloader = Dataloader(self.data_path, self.batch_size).traindataloader()
        self.test_dataloader = Dataloader(self.data_path, self.batch_size).testdataloader()

        self.model = DeepNet()
        self._model = DeepNet()
        self.loss = loss
        metric = Metric()
        self.metric_list = [o for o in getmembers(metric) if isfunction(o[1])]

        self.name = []
        for m in self.metric_list:
            self.name.append(m[0])
        self.name.append('loss')
        self.train_record, self.test_record = dict(), dict()
        for i in range(len(self.name)):
            self.train_record[self.name[i]] = []
        self.test_record = copy.deepcopy(self.train_record)

        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

        self.model = self.model.to(self.device)
        self._model = self._model.to(self.device)

        def get_initial_vec_params(varas):
            _vars_size = [int(torch.prod(torch.tensor(list(var.size()))).item()) for var in varas]
            vec_vars_set = [torch.reshape(var, (-1, _vars_size[k])) for k, var in enumerate(varas)]
            _vec_params = torch.cat([vec_vars_set[k] for k in range(len(_vars_size))], dim=1)
            return _vec_params.detach().numpy()

        variables = list(filter(lambda par: par.requires_grad, self.model.parameters()))
        self.vec_params = get_initial_vec_params(variables)
        self.vars_size = [torch.prod(torch.tensor(list(var.size()))).item() for var in variables]
        self.num_params = sum(self.vars_size)
        self.vars_shape = [list(var.size()) for var in variables]
        self.ind2 = [sum(self.vars_size[:i + 1]) for i in range(len(variables))]
        self.ind1 = [0] + self.ind2[:-1]
        self.extractor = self.extract()

    @staticmethod
    def eval_metrics(metrics, output, target):
        _metrics = []
        for name, metric in metrics:
            _metrics.append(metric(output, target))
        return _metrics

    def extract(self):
        lr = np.array([[-0.1052]], dtype=np.float32)
        while True:
            train_loss = 0
            total = 0
            accumulative_metrics = [0] * len(self.metric_list)
            lr *= 0.95
            for batch_idx, data in enumerate(self.train_dataloader):
                inpt = data[0].to(self.device)
                tagt = data[1].to(self.device)

                output = self.model(inpt)
                lo = self.loss(output, tagt)
                for param in self.model.parameters():
                    lo += self.reg_val * torch.norm(param)
                lo.backward()

                _metrics = self.eval_metrics(self.metric_list, output, tagt)
                for i, m in enumerate(_metrics):
                    accumulative_metrics[i] += m

                total += len(tagt)
                avg_metrics = []
                for m in accumulative_metrics:
                    avg_metrics.append(m / total)

                train_loss += lo.item()
                avg_metrics.append(train_loss / (batch_idx + 1))
                for i, val in enumerate(avg_metrics):
                    self.train_record[self.name[i]].append(val)

                grads = [torch.reshape(para.grad, (1, -1)) for para in self.model.parameters()]
                vec_grads = torch.cat([grads[i] for i in range(len(grads))], dim=1).detach().numpy()
                yield vec_grads, lr*np.sqrt(np.inner(vec_grads, vec_grads).astype(np.float32)), self.train_record
                for p in self.model.parameters():
                    if p.grad is not None:
                        p.grad.detach_()
                        p.grad.zero_()

    def evaluate(self):
        with torch.no_grad():
            test_loss = 0
            total = 0
            accumulative_metrics = [0] * len(self.metric_list)
            lock.acquire()
            model_state_dict = copy.deepcopy(self.model.state_dict())
            lock.release()
            self._model.load_state_dict(model_state_dict, strict=True)
            self._model.eval()
            for batch_idx, data in enumerate(self.test_dataloader):
                inpt = data[0].to(self.device)
                tagt = data[1].to(self.device)
                output = self._model(inpt)
                lo = self.loss(output, tagt)
                for param in self._model.parameters():
                    lo += self.reg_val * torch.norm(param)

                _metrics = self.eval_metrics(self.metric_list, output, tagt)
                for i, m in enumerate(_metrics):
                    accumulative_metrics[i] += m

                total += len(tagt)
                avg_metrics = []
                for m in accumulative_metrics:
                    avg_metrics.append(m / total)

                test_loss += lo.item()
                avg_metrics.append(test_loss / (batch_idx + 1))
                for i, val in enumerate(avg_metrics):
                    self.test_record[self.name[i]].append(val)

            if avg_metrics[0] > self.best:
                self.best = avg_metrics[0]
                check_point_path = os.path.join(self.ckp_path, 'R%010d.ckp' % self.roomid)
                torch.save({'model_state_dict': self._model.state_dict()}, check_point_path)
        return self.test_record

    def recover_shape(self, _vec_params, _vars_shape, _ind1, _ind2):
        vec_params_tensor = torch.from_numpy(_vec_params)
        recovered_vars = [torch.reshape(vec_params_tensor[0][ind[0]:ind[1]], shape=tuple(_vars_shape[k]))
                          for k, ind in enumerate(zip(_ind1, _ind2))]
        return recovered_vars

    def apply(self, params):
        recovered_params = self.recover_shape(params, self.vars_shape, self.ind1, self.ind2)
        lock.acquire()
        for i, param in enumerate(self.model.parameters()):
            param.data = recovered_params[i]
        lock.release()
