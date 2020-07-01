import os
import cv2
import h5py
import json
import shutil
import numpy as np
from pathlib import Path
import ruamel.yaml as yaml
import numpy.testing as npt
from unittest import TestCase
from moseq2_extract.cli import find_roi
from moseq2_extract.io.image import read_image
from tempfile import TemporaryDirectory, NamedTemporaryFile
from moseq2_extract.tests.integration_tests.test_cli import write_fake_movie
from moseq2_extract.util import gen_batch_sequence, load_metadata, load_timestamps,\
    select_strel, scalar_attributes, dict_to_h5, click_param_annot, \
    get_bucket_center, make_gradient, graduate_dilated_wall_area, convert_raw_to_avi_function, \
    recursive_find_h5s, clean_file_str, load_textdata, time_str_for_filename, build_path, read_yaml

class testExtractUtils(TestCase):

    def test_build_path(self):
        out = build_path({'test1': 'value', 'test2': 'value2'}, '{test1}_{test2}')
        assert out == 'value_value2'

    def test_read_yaml(self):

        test_file = 'data/config.yaml'
        test_dict = read_yaml(test_file)

        with open(test_file, 'r') as f:
            truth_dict = yaml.safe_load(f)

        assert truth_dict == test_dict

    def test_clean_file_str(self):
        test_name = 'd<a:t\\t"a'
        truth_out = 'd-a-t-t-a'

        test_out = clean_file_str(test_name)
        assert truth_out == test_out

    def test_load_textdata(self):
        data_file = 'data/depth_ts.txt'

        data, timestamps = load_textdata(data_file, np.uint8)
        assert data.all() != None
        assert timestamps.all() != None
        assert len(data) == len(timestamps)

    def test_time_str_for_filename(self):

        test_out = time_str_for_filename('12:12:12')
        truth_out = '12-12-12'
        assert test_out == truth_out

    def test_recursive_find_h5s(self):

        h5s, dicts, yamls = recursive_find_h5s('data/')
        assert len(h5s) == len(dicts) == len(yamls) > 0

    def test_gen_batch_sequence(self):

        tmp_list = [range(0, 10),
                    range(5, 15),
                    range(10, 20),
                    range(15, 25)]

        gen_list = list(gen_batch_sequence(25, 10, 5))

        assert(gen_list == tmp_list)


    def test_load_timestamps(self):

        with TemporaryDirectory() as tmp:
            txt_path = NamedTemporaryFile(prefix=tmp+'/', suffix=".txt")

            tmp_timestamps = np.arange(0, 5, .05)
            with open(txt_path.name, 'w') as f:
                for timestamp in tmp_timestamps:
                    print('{}'.format(str(timestamp)), file=f)

            loaded_timestamps = load_timestamps(txt_path.name)
            npt.assert_almost_equal(loaded_timestamps, tmp_timestamps, 10)

    def test_load_metadata(self):

        tmp_dict = {
            'test': 'test2'
        }

        with TemporaryDirectory() as tmp:
            json_file = NamedTemporaryFile(prefix=tmp+'/', suffix=".json")
            with open(json_file.name, 'w') as f:
                json.dump(tmp_dict, f)

            loaded_dict = load_metadata(json_file.name)

            assert(loaded_dict == tmp_dict)

    def test_convert_raw_to_avi(self):

        with TemporaryDirectory() as tmp:
            # writing a file to test following pipeline
            data_path = Path(NamedTemporaryFile(prefix=tmp+'/', suffix=".dat").name)

            write_fake_movie(data_path)

            convert_raw_to_avi_function(str(data_path))
            assert Path(str(data_path).replace('.dat', '.avi')).is_file()

    def test_select_strel(self):

        strel = select_strel('ellipse', size=(9, 9))
        npt.assert_equal(strel, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))

        strel = select_strel('rectangle', size=(9, 9))
        npt.assert_equal(strel, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))

        strel = select_strel('sdfdfsf', size=(9, 9))
        npt.assert_equal(strel, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))


    def test_scalar_attributes(self):

        dct = scalar_attributes()

        assert(dct is not None)


    def test_dict_to_h5(self):

        tmp_dic = {
            'subdict': {
                'sd_tuple': (0,1),
                'sd_string': 'quick brown fox',
                'sd_integer': 1,
                'sd_float': 1.0,
                'sd_bool': False,
                'sd_list': [1,2,3],
            },
            'tuple': (0,1),
            'string': 'quick brown fox',
            'integer': 1,
            'float': 1.0,
            'bool': False,
            'list': [1,2,3],
        }
        with TemporaryDirectory() as tmp:
            fpath = NamedTemporaryFile(prefix=tmp+'/', suffix=".h5")
            with h5py.File(fpath.name, 'w') as f:
                dict_to_h5(f, tmp_dic, tmp)

            def h5_to_dict(h5file, path):
                ans = {}
                if not path.endswith('/'):
                    path = path + '/'
                for key, item in h5file[path].items():
                    if type(item) is h5py.Dataset:
                        ans[key] = item[()]
                    elif type(item) is h5py.Group:
                        ans[key] = h5_to_dict(h5file, path + key + '/')
                return ans

            with h5py.File(fpath.name, 'r') as f:
                result = h5_to_dict(f, tmp)
            npt.assert_equal(result, tmp_dic)

    def test_get_bucket_center(self):
        img = read_image('data/tiffs/bground_bucket.tiff')
        roi = read_image('data/tiffs/roi_bucket_01.tiff')
        true_depth = np.median(img[roi > 0])

        x, y = get_bucket_center(img, true_depth)

        assert isinstance(x, int)
        assert isinstance(y, int)

        assert x > 0 and x < img.shape[1]
        assert y > 0 and y < img.shape[0]


    def test_make_gradient(self):
        img = read_image('data/tiffs/bground_bucket.tiff')
        width = img.shape[1]
        height = img.shape[0]
        xc = int(img.shape[1]/ 2)
        yc = int(img.shape[0] / 2)
        radx = int(img.shape[1] / 2)
        rady = int(img.shape[0] / 2)
        theta = 0

        grad = make_gradient(width, height, xc, yc, radx, rady, theta)
        assert grad[grad >= 0.08].all() == True
        assert grad[grad <= 0.8].all() == True

    def test_graduate_dilated_wall_area(self):
        img = read_image('data/tiffs/bground_bucket.tiff')
        roi = read_image('data/tiffs/roi_bucket_01.tiff')
        true_depth = np.median(img[roi > 0])

        config_data = {}
        strel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        output_dir = 'data/tiffs/'

        new_bg = graduate_dilated_wall_area(img, config_data, strel_dilate, true_depth, output_dir)

        assert new_bg.all() != img.all()
        assert np.median(new_bg) > np.median(img)
        assert os.path.exists('data/tiffs/new_bg.tiff')
        os.remove('data/tiffs/new_bg.tiff')

    def test_click_param_annot(self):
        ref_dict = {
            'bg_roi_dilate': 'Size of strel to dilate roi',
            'bg_roi_shape': 'Shape to use to dilate roi (ellipse or rect)',
            'bg_roi_index': 'Index of which background mask(s) to use',
            'bg_roi_weights': 'ROI feature weighting (area, extent, dist)',
            'bg_roi_depth_range': 'Range to search for floor of arena (in mm)',
            'bg_roi_gradient_filter': 'Exclude walls with gradient filtering',
            'bg_roi_gradient_threshold': 'Gradient must be < this to include points',
            'bg_roi_gradient_kernel': 'Kernel size for Sobel gradient filtering',
            'bg_sort_roi_by_position': 'Sort ROIs by position',
            'bg_sort_roi_by_position_max_rois': 'Max original ROIs to sort by position',
            'bg_roi_fill_holes': 'Fill holes in ROI',
            'dilate_iterations': 'Number of dilation iterations to increase bucket floor size.',
            'output_dir': 'Output directory to save the results h5 file',
            'use_plane_bground': 'Use a plane fit for the background. Useful for mice that don\'t move much',
            'config_file': None
        }
        test_dict = click_param_annot(find_roi)
        npt.assert_equal(ref_dict, test_dict)