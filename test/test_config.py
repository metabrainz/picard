from test.picardtestcase import PicardTestCase

from picard import config


class CommonTests:

    class CommonOptionTest(PicardTestCase):
        opt_type = config.Option
        default_value = 'somevalue'

        def setUp(self):
            self.opt_type.registry = {}

        def test_constructor(self):
            opt = self.opt_type('test', 'option1', self.default_value)
            self.assertEqual('test', opt.section)
            self.assertEqual('option1', opt.name)
            self.assertEqual(self.default_value, opt.default)

        def test_registry(self):
            opt = self.opt_type('test', 'option1', self.default_value)
            self.assertEqual(opt, self.opt_type.get('test', 'option1'))


class OptionTest(CommonTests.CommonOptionTest):

    def test_default_convert(self):
        for default in ['somevalue', True, [], tuple(), 42]:
            opt = config.Option('test', 'option1', default)
            self.assertEqual(type(default), opt.convert)
            self.assertEqual(default, opt.convert(default))


class TextOptionTest(CommonTests.CommonOptionTest):
    opt_type = config.TextOption
    default_value = 'test'

    def _test_convert(self, obj):
        self.assertEqual('', obj.convert(''))
        self.assertEqual('test', obj.convert('test'))
        self.assertEqual('42', obj.convert(42))

    def test_convert_instance(self):
        opt = self.opt_type('test', 'option1', self.default_value)
        self._test_convert(opt)

    def test_convert_static(self):
        self._test_convert(self.opt_type)


class BoolOptionTest(CommonTests.CommonOptionTest):
    opt_type = config.BoolOption
    default_value = False

    def _test_convert(self, obj):
        self.assertTrue(obj.convert(True))
        self.assertTrue(obj.convert('true'))
        self.assertFalse(obj.convert(None))
        self.assertFalse(obj.convert('unknown'))
        self.assertFalse(obj.convert('false'))

    def test_convert_instance(self):
        opt = self.opt_type('test', 'option1', self.default_value)
        self._test_convert(opt)

    def test_convert_static(self):
        self._test_convert(self.opt_type)


class IntOptionTest(CommonTests.CommonOptionTest):
    opt_type = config.IntOption
    default_value = 42

    def _test_convert(self, obj):
        self.assertEqual(42, obj.convert(42))
        self.assertEqual(42, obj.convert('42'))

    def test_convert_instance(self):
        opt = self.opt_type('test', 'option1', self.default_value)
        self._test_convert(opt)

    def test_convert_static(self):
        self._test_convert(self.opt_type)


class FloatOptionTest(CommonTests.CommonOptionTest):
    opt_type = config.FloatOption
    default_value = 42.5

    def _test_convert(self, obj):
        self.assertEqual(42.5, obj.convert(42.5))
        self.assertEqual(42.5, obj.convert('42.5'))

    def test_convert_instance(self):
        opt = self.opt_type('test', 'option1', self.default_value)
        self._test_convert(opt)

    def test_convert_static(self):
        self._test_convert(self.opt_type)


class ListOptionTest(CommonTests.CommonOptionTest):
    opt_type = config.ListOption
    default_value = ['somevalue']

    def _test_convert(self, obj):
        self.assertEqual([], obj.convert([]))
        self.assertEqual(['a', 'b', 'c'], obj.convert(('a', 'b', 'c')))
        self.assertEqual(['a', 'b', 'c'], obj.convert('abc'))

    def test_convert_instance(self):
        opt = self.opt_type('test', 'option1', self.default_value)
        self._test_convert(opt)

    def test_convert_static(self):
        self._test_convert(self.opt_type)


class IntListOptionTest(CommonTests.CommonOptionTest):
    opt_type = config.IntListOption
    default_value = [1, 2, 3]

    def _test_convert(self, obj):
        self.assertEqual([], obj.convert([]))
        self.assertEqual([1, 2, 3], obj.convert(('1', '2', '3')))

    def test_convert_instance(self):
        opt = self.opt_type('test', 'option1', self.default_value)
        self._test_convert(opt)

    def test_convert_static(self):
        self._test_convert(self.opt_type)
