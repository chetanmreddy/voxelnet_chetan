import numpy as np

from mmdet.datasets.builder import PIPELINES
from mmdet.datasets.pipelines import Compose, RandomFlip


@PIPELINES.register_module()
class NuScenesMultiViewPipeline:
    def __init__(self, transforms):
        self.transforms = Compose(transforms)

    def __call__(self, results):
        aug_data = []
        for i in range(len(results['img_info'])):
            _results = dict()
            for key in ['img_prefix', 'img_info', 'lidar2img']:
                _results[key] = results[key][i]
            for key in ['box_type_3d', 'box_mode_3d']:
                _results[key] = results[key]
            aug_data.append(self.transforms(_results))
        # list of dict to dict of list
        aug_data_dict = {key: [] for key in aug_data[0]}
        for data in aug_data:
            for key, val in data.items():
                aug_data_dict[key].append(val)
        return aug_data_dict


@PIPELINES.register_module()
class ScanNetMultiViewPipeline:
    def __init__(self, transforms, n_images):
        self.transforms = Compose(transforms)
        self.n_images = n_images

    def __call__(self, results):
        imgs = []
        extrinsics = []
        # set flip flag for all images
        flip = False
        flip_direction = 'horizontal'
        for transform in self.transforms.transforms:
            if isinstance(transform, RandomFlip):
                if np.random.random() > .5:
                    flip = True

        ids = np.arange(len(results['img_info']))
        replace = True if self.n_images > len(ids) else False
        ids = np.random.choice(ids, self.n_images, replace=replace)
        for i in ids.tolist():
            _results = dict(flip=flip, flip_direction=flip_direction)
            for key in ['img_prefix', 'img_info']:
                _results[key] = results[key][i]
            _results = self.transforms(_results)
            imgs.append(_results['img'])
            extrinsics.append(results['lidar2img']['extrinsic'][i])
        for key in _results.keys():
            if key not in ['img', 'lidar2img', 'img_prefix', 'img_info']:
                results[key] = _results[key]

        # this can not be done before because of absence of 'ori_shape'
        if results['flip']:
            results['lidar2img']['intrinsic'][0] *= -1
            results['lidar2img']['intrinsic'][0, 2] += results['ori_shape'][1]
        results['img'] = imgs
        results['lidar2img']['extrinsic'] = extrinsics
        return results


@PIPELINES.register_module()
class RandomShiftOrigin:
    def __init__(self, threshold):
        self.threshold = threshold

    def __call__(self, results):
        shift = np.random.uniform(-self.threshold, self.threshold, 3)
        results['lidar2img']['origin'] += shift
        return results
