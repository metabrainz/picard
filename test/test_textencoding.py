# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2014, 2017 Sophist-UK
# Copyright (C) 2015, 2018, 2020-2022 Laurent Monin
# Copyright (C) 2017 Ville Skyttä
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018-2019, 2021, 2023 Philipp Wolfer
# Copyright (C) 2020 Undearius
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from test.picardtestcase import PicardTestCase

from picard import util
from picard.const.sys import IS_WIN


# Set the value to true below to show the coverage of Latin characters
show_latin2ascii_coverage = False

compatibility_from = (
    "\u0132\u0133\u017F\u01C7\u01C8\u01C9\u01CA\u01CB\u01CC\u01F1"  # ĲĳſǇǈǉǊǋǌǱ
    "\u01F2\u01F3\uFB00\uFB01\uFB02\uFB03\uFB04\uFB05\uFB06\uFF21"  # ǲǳﬀﬁﬂﬃﬄﬅﬆＡ
    "\uFF22\uFF23\uFF24\uFF25\uFF26\uFF27\uFF28\uFF29\uFF2A\uFF2B"  # ＢＣＤＥＦＧＨＩＪＫ
    "\uFF2C\uFF2D\uFF2E\uFF2F\uFF30\uFF31\uFF32\uFF33\uFF34\uFF35"  # ＬＭＮＯＰＱＲＳＴＵ
    "\uFF36\uFF37\uFF38\uFF39\uFF3A\uFF41\uFF42\uFF43\uFF44\uFF45"  # ＶＷＸＹＺａｂｃｄｅ
    "\uFF46\uFF47\uFF48\uFF49\uFF4A\uFF4B\uFF4C\uFF4D\uFF4E\uFF4F"  # ｆｇｈｉｊｋｌｍｎｏ
    "\uFF50\uFF51\uFF52\uFF53\uFF54\uFF55\uFF56\uFF57\uFF58\uFF59"  # ｐｑｒｓｔｕｖｗｘｙ
    "\uFF5A\u2100\u2101\u2102\u2105\u2106\u210A\u210B\u210C\u210D"  # ｚ℀℁ℂ℅℆ℊℋℌℍ
    "\u210E\u2110\u2111\u2112\u2113\u2115\u2116\u2119\u211A\u211B"  # ℎℐℑℒℓℕ№ℙℚℛ
    "\u211C\u211D\u2121\u2124\u2128\u212C\u212D\u212F\u2130\u2131"  # ℜℝ℡ℤℨℬℭℯℰℱ
    "\u2133\u2134\u2139\u213B\u2145\u2146\u2147\u2148\u2149\u3371"  # ℳℴℹ℻ⅅⅆⅇⅈⅉ㍱
    "\u3372\u3373\u3374\u3375\u3376\u3377\u337A\u3380\u3381\u3383"  # ㍲㍳㍴㍵㍶㍷㍺㎀㎁㎃
    "\u3384\u3385\u3386\u3387\u3388\u3389\u338A\u338B\u338E\u338F"  # ㎄㎅㎆㎇㎈㎉㎊㎋㎎㎏
    "\u3390\u3391\u3392\u3393\u3394\u3399\u339A\u339C\u339D\u339E"  # ㎐㎑㎒㎓㎔㎙㎚㎜㎝㎞
    "\u33A9\u33AA\u33AB\u33AC\u33AD\u33B0\u33B1\u33B3\u33B4\u33B5"  # ㎩㎪㎫㎬㎭㎰㎱㎳㎴㎵
    "\u33B7\u33B8\u33B9\u33BA\u33BB\u33BD\u33BE\u33BF\u33C2\u33C3"  # ㎷㎸㎹㎺㎻㎽㎾㎿㏂㏃
    "\u33C4\u33C5\u33C7\u33C8\u33C9\u33CA\u33CB\u33CC\u33CD\u33CE"  # ㏄㏅㏇㏈㏉㏊㏋㏌㏍㏎
    "\u33CF\u33D0\u33D1\u33D2\u33D3\u33D4\u33D5\u33D6\u33D7\u33D8"  # ㏏㏐㏑㏒㏓㏔㏕㏖㏗㏘
    "\u33D9\u33DA\u33DB\u33DC\u33DD\u249C\u249D\u249E\u249F\u24A0"  # ㏙㏚㏛㏜㏝⒜⒝⒞⒟⒠
    "\u24A1\u24A2\u24A3\u24A4\u24A5\u24A6\u24A7\u24A8\u24A9\u24AA"  # ⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪
    "\u24AB\u24AC\u24AD\u24AE\u24AF\u24B0\u24B1\u24B2\u24B3\u24B4"  # ⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴
    "\u24B5\u2160\u2161\u2162\u2163\u2164\u2165\u2166\u2167\u2168"  # ⒵ⅠⅡⅢⅣⅤⅥⅦⅧⅨ
    "\u2169\u216A\u216B\u216C\u216D\u216E\u216F\u2170\u2171\u2172"  # ⅩⅪⅫⅬⅭⅮⅯⅰⅱⅲ
    "\u2173\u2174\u2175\u2176\u2177\u2178\u2179\u217A\u217B\u217C"  # ⅳⅴⅵⅶⅷⅸⅹⅺⅻⅼ
    "\u217D\u217E\u217F\u2474\u2475\u2476\u2477\u2478\u2479\u247A"  # ⅽⅾⅿ⑴⑵⑶⑷⑸⑹⑺
    "\u247B\u247C\u247D\u247E\u247F\u2480\u2481\u2482\u2483\u2484"  # ⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄
    "\u2485\u2486\u2487\u2488\u2489\u248A\u248B\u248C\u248D\u248E"  # ⒅⒆⒇⒈⒉⒊⒋⒌⒍⒎
    "\u248F\u2490\u2491\u2492\u2493\u2494\u2495\u2496\u2497\u2498"  # ⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘
    "\u2499\u249A\u249B\uFF10\uFF11\uFF12\uFF13\uFF14\uFF15\uFF16"  # ⒙⒚⒛０１２３４５６
    "\uFF17\uFF18\uFF19\u2002\u2003\u2004\u2005\u2006\u2007\u2008"  # ７８９\u2002\u2003\u2004\u2005\u2006\u2007\u2008
    "\u2009\u200A\u205F\uFF02\uFF07\uFE63\uFF0D\u2024\u2025\u2026"  # \u2009\u200A\u205F＂＇﹣－․‥…
    "\u203C\u2047\u2048\u2049\uFE10\uFE13\uFE14\uFE15\uFE16\uFE19"  # ‼⁇⁈⁉︐︓︔︕︖︙
    "\uFE30\uFE35\uFE36\uFE37\uFE38\uFE47\uFE48\uFE50\uFE52\uFE54"  # ︰︵︶︷︸﹇﹈﹐﹒﹔
    "\uFE55\uFE56\uFE57\uFE59\uFE5A\uFE5B\uFE5C\uFE5F\uFE60\uFE61"  # ﹕﹖﹗﹙﹚﹛﹜﹟﹠﹡
    "\uFE62\uFE64\uFE65\uFE66\uFE68\uFE69\uFE6A\uFE6B\uFF01\uFF03"  # ﹢﹤﹥﹦﹨﹩﹪﹫！＃
    "\uFF04\uFF05\uFF06\uFF08\uFF09\uFF0A\uFF0B\uFF0C\uFF0E\uFF0F"  # ＄％＆（）＊＋，．／
    "\uFF1A\uFF1B\uFF1C\uFF1D\uFF1E\uFF1F\uFF20\uFF3B\uFF3C\uFF3D"  # ：；＜＝＞？＠［＼］
    "\uFF3E\uFF3F\uFF40\uFF5B\uFF5C\uFF5D\uFF5E\u2A74\u2A75\u2A76"  # ＾＿｀｛｜｝～⩴⩵⩶
)
compatibility_to = (
    "IJijsLJLjljNJNjnjDZDzdzfffiflffifflststABCDEFGHIJKLMNOPQRSTU"
    "VWXYZabcdefghijklmnopqrstuvwxyza/ca/sCc/oc/ugHHH"
    "hIILlNNoPQRRRTELZZBCeEFMoiFAXDdeijhPadaAUbaroVpcdmIUpAnAmA"
    "kAKBMBGBcalkcalpFnFmgkgHzkHzMHzGHzTHzfmnmmmcmkmPakPaMPaGParadpsnsmspVnVmVkVMVpWnWmWkWMWa.m.Bq"
    "cccdCo.dBGyhaHPinKKKMktlmlnloglxmbmilmolPHp.m.PPMPRsrSvWb(a)(b)(c)(d)(e)(f)(g)(h)(i)(j)(k)(l)(m)(n)(o)"
    "(p)(q)(r)(s)(t)(u)(v)(w)(x)(y)(z)IIIIIIIVVVIVIIVIIIIXXXIXIILCDMiiiiiiivvviviiviiiixxxixiil"
    "cdm(1)(2)(3)(4)(5)(6)(7)(8)(9)(10)(11)(12)(13)(14)(15)(16)(17)(18)(19)(20)1.2.3.4.5.6.7.8.9.10.11.12.13.14.15.16.17."
    "18.19.20.0123456789          \"'--......!!???!!?,:;!?..."
    "..(){}[],.;:?!(){}#&*+<>=\\$%@!#$%&()*+,./"
    ":;<=>?@[\\]^_`{|}~::======"
)
compatibility_from += (
    "\u1D00\u1D04\u1D05\u1D07\u1D0A\u1D0B\u1D0D\u1D0F\u1D18\u1D1B"  # ᴀᴄᴅᴇᴊᴋᴍᴏᴘᴛ
    "\u1D1C\u1D20\u1D21\u1D22\u3007\u00A0\u3000"                    # ᴜᴠᴡᴢ〇\u00A0\u3000
)
compatibility_to += "ACDEJKMOPTUVWZ0  "
punctuation_from = (
    "\u2018\u2019\u201A\u201B\u201C\u201D\u201E\u201F\u2032\u301D"  # ‘’‚‛“”„‟′〝
    "\u301E\u00AB\u00BB\u2039\u203A\u00AD\u2010\u2012\u2013\u2014"  # 〞«»‹›\u00AD‐‒–—
    "\u2015\u2016\u2044\u2045\u2046\u204E\u3008\u3009\u300A\u300B"  # ―‖⁄⁅⁆⁎〈〉《》
    "\u3014\u3015\u3018\u3019\u301A\u301B\u2212\u2215\u2216\u2223"  # 〔〕〘〙〚〛−∕∖∣
    "\u2225\u226A\u226B\u2985\u2986\u2022\u200B"                    # ∥≪≫⦅⦆•·
)
punctuation_to = "''''\"\"\"\"'\"\"<<>><>-----||/[]*<><<>>[][][]-/\\|||<<>>(())-"
combinations_from = (
    "\u00C6\u00D0\u00D8\u00DE\u00DF\u00E6\u00F0\u00F8\u00FE\u0110"  # ÆÐØÞßæðøþĐ
    "\u0111\u0126\u0127\u0131\u0138\u0141\u0142\u014A\u014B\u0152"  # đĦħıĸŁłŊŋŒ
    "\u0153\u0166\u0167\u0180\u0181\u0182\u0183\u0187\u0188\u0189"  # œŦŧƀƁƂƃƇƈƉ
    "\u018A\u018B\u018C\u0190\u0191\u0192\u0193\u0195\u0196\u0197"  # ƊƋƌƐƑƒƓƕƖƗ
    "\u0198\u0199\u019A\u019D\u019E\u01A2\u01A3\u01A4\u01A5\u01AB"  # ƘƙƚƝƞƢƣƤƥƫ
    "\u01AC\u01AD\u01AE\u01B2\u01B3\u01B4\u01B5\u01B6\u01E4\u01E5"  # ƬƭƮƲƳƴƵƶǤǥ
    "\u0221\u0224\u0225\u0234\u0235\u0236\u0237\u0238\u0239\u023A"  # ȡȤȥȴȵȶȷȸȹȺ
    "\u023B\u023C\u023D\u023E\u023F\u0240\u0243\u0244\u0246\u0247"  # ȻȼȽȾȿɀɃɄɆɇ
    "\u0248\u0249\u024C\u024D\u024E\u024F\u0253\u0255\u0256\u0257"  # ɈɉɌɍɎɏɓɕɖɗ
    "\u025B\u025F\u0260\u0261\u0262\u0266\u0267\u0268\u026A\u026B"  # ɛɟɠɡɢɦɧɨɪɫ
    "\u026C\u026D\u0271\u0272\u0273\u0274\u027C\u027D\u027E\u0280"  # ɬɭɱɲɳɴɼɽɾʀ
    "\u0282\u0288\u0289\u028B\u028F\u0290\u0291\u0299\u029B\u029C"  # ʂʈʉʋʏʐʑʙʛʜ
    "\u029D\u029F\u02A0\u02A3\u02A5\u02A6\u02AA\u02AB\u1D03\u1D06"  # ʝʟʠʣʥʦʪʫᴃᴆ
    "\u1D0C\u1D6B\u1D6C\u1D6D\u1D6E\u1D6F\u1D70\u1D71\u1D72\u1D73"  # ᴌᵫᵬᵭᵮᵯᵰᵱᵲᵳ
    "\u1D74\u1D75\u1D76\u1D7A\u1D7B\u1D7D\u1D7E\u1D80\u1D81\u1D82"  # ᵴᵵᵶᵺᵻᵽᵾᶀᶁᶂ
    "\u1D83\u1D84\u1D85\u1D86\u1D87\u1D88\u1D89\u1D8A\u1D8C\u1D8D"  # ᶃᶄᶅᶆᶇᶈᶉᶊᶌᶍ
    "\u1D8E\u1D8F\u1D91\u1D92\u1D93\u1D96\u1D99\u1E9C\u1E9D\u1E9E"  # ᶎᶏᶑᶒᶓᶖᶙẜẝẞ
    "\u1EFA\u1EFB\u1EFC\u1EFD\u1EFE\u1EFF\u00A9\u00AE\u20A0\u20A2"  # ỺỻỼỽỾỿ©®₠₢
    "\u20A3\u20A4\u20A7\u20BA\u20B9\u211E\u3001\u3002\u00D7\u00F7"  # ₣₤₧₺₹℞、。×÷
    "\u00B7\u1E9F\u0184\u0185\u01BE"                                # ·ẟƄƅƾ
)
combinations_to = (
    "AEDOETHssaedoethDdHhiqLlNnOEoeTtbBBbCcDDDdEFfGhvII"
    "KklNnGHghPptTtTVYyZzGgdZzlntjdbqpACcLTszBUEe"
    "JjRrYybcddejggGhhiIlllmnnNrrrRstuvYzzBGH"
    "jLqdzdztslslzBDLuebdfmnprrstzthIpUbdfgklmnprsvx"
    "zadeeiussSSLLllVvYy(C)(R)CECrFr.L.PtsTLRsRx,.x/.ddHhts"
)
ascii_chars = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"


class CompatibilityTest(PicardTestCase):

    def test_correct(self):
        self.maxDiff = None
        self.assertEqual(util.textencoding.unicode_simplify_compatibility(compatibility_from), compatibility_to)
        self.assertEqual(util.textencoding.unicode_simplify_compatibility(punctuation_from), punctuation_from)
        self.assertEqual(util.textencoding.unicode_simplify_compatibility(combinations_from), combinations_from)
        self.assertEqual(util.textencoding.unicode_simplify_compatibility(ascii_chars), ascii_chars)

    def test_pathsave(self):
        self.assertEqual(util.textencoding.unicode_simplify_compatibility('\uff0f', pathsave=True), '_')

    def test_incorrect(self):
        pass


class PunctuationTest(PicardTestCase):

    def test_correct(self):
        self.maxDiff = None
        self.assertEqual(util.textencoding.unicode_simplify_punctuation(compatibility_from), compatibility_from)
        self.assertEqual(util.textencoding.unicode_simplify_punctuation(punctuation_from), punctuation_to)
        self.assertEqual(util.textencoding.unicode_simplify_punctuation(combinations_from), combinations_from)
        self.assertEqual(util.textencoding.unicode_simplify_punctuation(ascii_chars), ascii_chars)

    def test_pathsave(self):
        self.assertEqual(util.textencoding.unicode_simplify_punctuation('\u2215\u2216', True), '__' if IS_WIN else '_\\')
        self.assertEqual(util.textencoding.unicode_simplify_punctuation('/\\\u2215\u2216', True), '/\\__' if IS_WIN else '/\\_\\')

    def test_pathsave_win_compat(self):
        self.assertEqual(util.textencoding.unicode_simplify_punctuation('\u2215\u2216', True, True), '__')
        self.assertEqual(util.textencoding.unicode_simplify_punctuation('/\\\u2215\u2216', True, True), '/\\__')

    def test_incorrect(self):
        pass


class CombinationsTest(PicardTestCase):

    def test_correct(self):
        self.maxDiff = None
        self.assertEqual(util.textencoding.unicode_simplify_combinations(combinations_from), combinations_to)
        self.assertEqual(util.textencoding.unicode_simplify_combinations(compatibility_from), compatibility_from)
        self.assertEqual(util.textencoding.unicode_simplify_combinations(punctuation_from), punctuation_from)
        self.assertEqual(util.textencoding.unicode_simplify_combinations(ascii_chars), ascii_chars)

    def test_pathsave(self):
        self.assertEqual(util.textencoding.unicode_simplify_combinations('8½', True), '8 1_2')
        self.assertEqual(util.textencoding.unicode_simplify_combinations('8/\\½', True), '8/\\ 1_2')

    def test_incorrect(self):
        pass


class AsciiPunctTest(PicardTestCase):

    def test_correct(self):
        self.assertEqual(util.textencoding.asciipunct("‘Test’"), "'Test'")  # Quotations
        self.assertEqual(util.textencoding.asciipunct("“Test”"), "\"Test\"")  # Quotations
        self.assertEqual(util.textencoding.asciipunct("1′6″"), "1'6\"")  # Quotations
        self.assertEqual(util.textencoding.asciipunct("…"), "...")  # Ellipses
        self.assertEqual(util.textencoding.asciipunct("\u2024"), ".")  # ONE DOT LEADER
        self.assertEqual(util.textencoding.asciipunct("\u2025"), "..")  # TWO DOT LEADER

    def test_incorrect(self):
        pass


class UnaccentTest(PicardTestCase):

    def test_correct(self):
        self.assertEqual(util.textencoding.unaccent("Lukáš"), "Lukas")
        self.assertEqual(util.textencoding.unaccent("Björk"), "Bjork")
        self.assertEqual(util.textencoding.unaccent("小室哲哉"), "小室哲哉")

    def test_incorrect(self):
        self.assertNotEqual(util.textencoding.unaccent("Björk"), "Björk")
        self.assertNotEqual(util.textencoding.unaccent("小室哲哉"), "Tetsuya Komuro")
        self.assertNotEqual(util.textencoding.unaccent("Trentemøller"), "Trentemoller")
        self.assertNotEqual(util.textencoding.unaccent("Ænima"), "AEnima")
        self.assertNotEqual(util.textencoding.unaccent("ænima"), "aenima")


class ReplaceNonAsciiTest(PicardTestCase):

    def test_correct(self):
        self.assertEqual(util.textencoding.replace_non_ascii("Lukáš"), "Lukas")
        self.assertEqual(util.textencoding.replace_non_ascii("Björk"), "Bjork")
        self.assertEqual(util.textencoding.replace_non_ascii("Trentemøller"), "Trentemoeller")
        self.assertEqual(util.textencoding.replace_non_ascii("Ænima"), "AEnima")
        self.assertEqual(util.textencoding.replace_non_ascii("ænima"), "aenima")
        self.assertEqual(util.textencoding.replace_non_ascii("小室哲哉"), "____")
        self.assertEqual(util.textencoding.replace_non_ascii("ᴀᴄᴇ"), "ACE")  # Latin Letter Small
        self.assertEqual(util.textencoding.replace_non_ascii("Ａｂｃ"), "Abc")  # Fullwidth Latin
        self.assertEqual(util.textencoding.replace_non_ascii("500㎏,2㎓"), "500kg,2GHz")  # Technical
        self.assertEqual(util.textencoding.replace_non_ascii("⒜⒝⒞"), "(a)(b)(c)")  # Parenthesised Latin
        self.assertEqual(util.textencoding.replace_non_ascii("ⅯⅯⅩⅣ"), "MMXIV")  # Roman numerals
        self.assertEqual(util.textencoding.replace_non_ascii("ⅿⅿⅹⅳ"), "mmxiv")  # Roman numerals small
        self.assertEqual(util.textencoding.replace_non_ascii("⑴⑵⑶"), "(1)(2)(3)")  # Parenthesised numbers
        self.assertEqual(util.textencoding.replace_non_ascii("⒈ ⒉ ⒊"), "1. 2. 3.")  # Digit full stop
        self.assertEqual(util.textencoding.replace_non_ascii("１２３"), "123")  # Fullwidth digits
        self.assertEqual(util.textencoding.replace_non_ascii("\u2216\u2044\u2215\uff0f"), "\\///")  # Slashes

    def test_pathsave(self):
        expected = '____/8 1_2\\' if IS_WIN else '\\___/8 1_2\\'
        self.assertEqual(util.textencoding.replace_non_ascii('\u2216\u2044\u2215\uff0f/8½\\', pathsave=True), expected)

    def test_win_compat(self):
        self.assertEqual(util.textencoding.replace_non_ascii('\u2216\u2044\u2215\uff0f/8½\\', pathsave=True, win_compat=True), '____/8 1_2\\')

    def test_incorrect(self):
        self.assertNotEqual(util.textencoding.replace_non_ascii("Lukáš"), "Lukáš")
        self.assertNotEqual(util.textencoding.replace_non_ascii("Lukáš"), "Luk____")


if show_latin2ascii_coverage:
    # The following code set blocks are taken from:
    # http://en.wikipedia.org/wiki/Latin_script_in_Unicode
    latin_1 = "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"
    latin_a = "ĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿ" \
              "ŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽž"
    latin_b = "ƀƁƂƃƄƅƆƇƈƉƊƋƌƍƎƏƐƑƒƓƔƕƖƗƘƙƚƛƜƝƞƟƠơƢƣƤƥƦƧƨƩƪƫƬƭƮƯưƱƲƳƴƵƶƷƸƹƺƻƼƽƾƿ" \
              "ǀǁǂǃǄǅǆǇǈǉǊǋǌǍǎǏǐǑǒǓǔǕǖǗǘǙǚǛǜǝǞǟǠǡǢǣǤǥǦǧǨǩǪǫǬǭǮǯǰǱǲǳǴǵǶǷǸǹǺǻǼǽǾǿ" \
              "ȀȁȂȃȄȅȆȇȈȉȊȋȌȍȎȏȐȑȒȓȔȕȖȗȘșȚțȜȝȞȟȠȡȢȣȤȥȦȧȨȩȪȫȬȭȮȯȰȱȲȳȴȵȶȷȸȹȺȻȼȽȾȿ" \
              "ɀɁɂɃɄɅɆɇɈɉɊɋɌɍɎɏ"
    ipa_ext = "ɐɑɒɓɔɕɖɗɘəɚɛɜɝɞɟɠɡɢɣɤɥɦɧɨɩɪɫɬɭɮɯɰɱɲɳɴɵɶɷɸɹɺɻɼɽɾɿʀʁʂʃʄʅʆʇʈʉʊʋʌʍʎʏ" \
              "ʐʑʒʓʔʕʖʗʘʙʚʛʜʝʞʟʠʡʢʣʤʥʦʧʨʩʪʫʬʭʮʯ"
    phonetic = "ᴀᴁᴂᴃᴄᴅᴆᴇᴈᴉᴊᴋᴌᴍᴎᴏᴐᴑᴒᴓᴔᴕᴖᴗᴘᴙᴚᴛᴜᴝᴞᴟᴠᴡᴢᴣᴤᴥᴦᴧᴨᴩᴪᴫᴬᴭᴮᴯᴰᴱᴲᴳᴴᴵᴶᴷᴸᴹᴺᴻᴼᴽᴾᴿ" \
               "ᵀᵁᵂᵃᵄᵅᵆᵇᵈᵉᵊᵋᵌᵍᵎᵏᵐᵑᵒᵓᵔᵕᵖᵗᵘᵙᵚᵛᵜᵝᵞᵟᵠᵡᵢᵣᵤᵥᵦᵧᵨᵩᵪᵫᵬᵭᵮᵯᵰᵱᵲᵳᵴᵵᵶᵷᵸᵹᵺᵻᵼᵽᵾᵿ" \
               "ᶀᶁᶂᶃᶄᶅᶆᶇᶈᶉᶊᶋᶌᶍᶎᶏᶐᶑᶒᶓᶔᶕᶖᶗᶘᶙᶚᶛᶜᶝᶞᶟᶠᶡᶢᶣᶤᶥᶦᶧᶨᶩᶪᶫᶬᶭᶮᶯᶰᶱᶲᶳᶴᶵᶶᶷᶸᶹᶺᶻᶼᶽᶾᶿ"
    latin_ext_add = "ḀḁḂḃḄḅḆḇḈḉḊḋḌḍḎḏḐḑḒḓḔḕḖḗḘḙḚḛḜḝḞḟḠḡḢḣḤḤḦḧḨḩḪḫḬḭḮḯḰḱḲḳḴḵḶḷḸḹḺḻḼḽḾḿ" \
                    "ṀṁṂṃṄṅṆṇṈṉṊṋṌṍṎṏṐṑṒṓṔṕṖṗṘṙṚṛṜṝṞṟṠṡṢṣṤṥṦṧṨṩṪṫṬṭṮṯṰṱṲṳṴṵṶṷṸṹṺṻṼṽṾṿ" \
                    "ẀẁẂẃẄẅẆẇẈẉẊẋẌẍẎẏẐẑẒẓẔẕẖẗẘẙẚẛẜẝẞẟẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾế" \
                    "ỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹỺỻỼỽỾỿ"
    letter_like = "℀℁ℂ℃℄℅℆ℇ℈℉ℊℋℌℍℎℏℐℑℒℓ℔ℕ№℗℘ℙℚℛℜℝ℞℟℠℡™℣ℤ℥Ω℧ℨ℩KÅℬℭ℮ℯℰℱℲℳℴℵℶℷℸℹ℺℻ℼℽℾℿ" \
                  "⅀⅁⅂⅃⅄ⅅⅆⅇⅈⅉ⅊⅋⅌⅍ⅎ⅏"
    enclosed = "⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛⒜⒝⒞⒟⒠⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴⒵ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ" \
                "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ⓪⓫⓬⓭⓮⓯"

    print("The following lines show the coverage of Latin characters conversion to ascii.")
    print("Underscores are characters which currently do not have an ASCII representation.")
    print()
    print("latin-1:       ", util.textencoding.replace_non_ascii(latin_1))
    print("latin-1:       ", util.textencoding.replace_non_ascii(latin_1))
    print("latin-a:       ", util.textencoding.replace_non_ascii(latin_a))
    print("latin-b:       ", util.textencoding.replace_non_ascii(latin_b))
    print("ipa-ext:       ", util.textencoding.replace_non_ascii(ipa_ext))
    print("phonetic:      ", util.textencoding.replace_non_ascii(phonetic))
    print("latin-ext-add: ", util.textencoding.replace_non_ascii(latin_ext_add))
    print("letter-like:   ", util.textencoding.replace_non_ascii(letter_like))
    print("enclosed:      ", util.textencoding.replace_non_ascii(enclosed))
    print()
