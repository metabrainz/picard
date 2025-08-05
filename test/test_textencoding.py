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
    "\u0132\u0133\u017f\u01c7\u01c8\u01c9\u01ca\u01cb\u01cc\u01f1"  # ĲĳſǇǈǉǊǋǌǱ
    "\u01f2\u01f3\ufb00\ufb01\ufb02\ufb03\ufb04\ufb05\ufb06\uff21"  # ǲǳﬀﬁﬂﬃﬄﬅﬆＡ
    "\uff22\uff23\uff24\uff25\uff26\uff27\uff28\uff29\uff2a\uff2b"  # ＢＣＤＥＦＧＨＩＪＫ
    "\uff2c\uff2d\uff2e\uff2f\uff30\uff31\uff32\uff33\uff34\uff35"  # ＬＭＮＯＰＱＲＳＴＵ
    "\uff36\uff37\uff38\uff39\uff3a\uff41\uff42\uff43\uff44\uff45"  # ＶＷＸＹＺａｂｃｄｅ
    "\uff46\uff47\uff48\uff49\uff4a\uff4b\uff4c\uff4d\uff4e\uff4f"  # ｆｇｈｉｊｋｌｍｎｏ
    "\uff50\uff51\uff52\uff53\uff54\uff55\uff56\uff57\uff58\uff59"  # ｐｑｒｓｔｕｖｗｘｙ
    "\uff5a\u2100\u2101\u2102\u2105\u2106\u210a\u210b\u210c\u210d"  # ｚ℀℁ℂ℅℆ℊℋℌℍ
    "\u210e\u2110\u2111\u2112\u2113\u2115\u2116\u2119\u211a\u211b"  # ℎℐℑℒℓℕ№ℙℚℛ
    "\u211c\u211d\u2121\u2124\u2128\u212c\u212d\u212f\u2130\u2131"  # ℜℝ℡ℤℨℬℭℯℰℱ
    "\u2133\u2134\u2139\u213b\u2145\u2146\u2147\u2148\u2149\u3371"  # ℳℴℹ℻ⅅⅆⅇⅈⅉ㍱
    "\u3372\u3373\u3374\u3375\u3376\u3377\u337a\u3380\u3381\u3383"  # ㍲㍳㍴㍵㍶㍷㍺㎀㎁㎃
    "\u3384\u3385\u3386\u3387\u3388\u3389\u338a\u338b\u338e\u338f"  # ㎄㎅㎆㎇㎈㎉㎊㎋㎎㎏
    "\u3390\u3391\u3392\u3393\u3394\u3399\u339a\u339c\u339d\u339e"  # ㎐㎑㎒㎓㎔㎙㎚㎜㎝㎞
    "\u33a9\u33aa\u33ab\u33ac\u33ad\u33b0\u33b1\u33b3\u33b4\u33b5"  # ㎩㎪㎫㎬㎭㎰㎱㎳㎴㎵
    "\u33b7\u33b8\u33b9\u33ba\u33bb\u33bd\u33be\u33bf\u33c2\u33c3"  # ㎷㎸㎹㎺㎻㎽㎾㎿㏂㏃
    "\u33c4\u33c5\u33c7\u33c8\u33c9\u33ca\u33cb\u33cc\u33cd\u33ce"  # ㏄㏅㏇㏈㏉㏊㏋㏌㏍㏎
    "\u33cf\u33d0\u33d1\u33d2\u33d3\u33d4\u33d5\u33d6\u33d7\u33d8"  # ㏏㏐㏑㏒㏓㏔㏕㏖㏗㏘
    "\u33d9\u33da\u33db\u33dc\u33dd\u249c\u249d\u249e\u249f\u24a0"  # ㏙㏚㏛㏜㏝⒜⒝⒞⒟⒠
    "\u24a1\u24a2\u24a3\u24a4\u24a5\u24a6\u24a7\u24a8\u24a9\u24aa"  # ⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪
    "\u24ab\u24ac\u24ad\u24ae\u24af\u24b0\u24b1\u24b2\u24b3\u24b4"  # ⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴
    "\u24b5\u2160\u2161\u2162\u2163\u2164\u2165\u2166\u2167\u2168"  # ⒵ⅠⅡⅢⅣⅤⅥⅦⅧⅨ
    "\u2169\u216a\u216b\u216c\u216d\u216e\u216f\u2170\u2171\u2172"  # ⅩⅪⅫⅬⅭⅮⅯⅰⅱⅲ
    "\u2173\u2174\u2175\u2176\u2177\u2178\u2179\u217a\u217b\u217c"  # ⅳⅴⅵⅶⅷⅸⅹⅺⅻⅼ
    "\u217d\u217e\u217f\u2474\u2475\u2476\u2477\u2478\u2479\u247a"  # ⅽⅾⅿ⑴⑵⑶⑷⑸⑹⑺
    "\u247b\u247c\u247d\u247e\u247f\u2480\u2481\u2482\u2483\u2484"  # ⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄
    "\u2485\u2486\u2487\u2488\u2489\u248a\u248b\u248c\u248d\u248e"  # ⒅⒆⒇⒈⒉⒊⒋⒌⒍⒎
    "\u248f\u2490\u2491\u2492\u2493\u2494\u2495\u2496\u2497\u2498"  # ⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘
    "\u2499\u249a\u249b\uff10\uff11\uff12\uff13\uff14\uff15\uff16"  # ⒙⒚⒛０１２３４５６
    "\uff17\uff18\uff19\u2002\u2003\u2004\u2005\u2006\u2007\u2008"  # ７８９\u2002\u2003\u2004\u2005\u2006\u2007\u2008
    "\u2009\u200a\u205f\uff02\uff07\ufe63\uff0d\u2024\u2025\u2026"  # \u2009\u200A\u205F＂＇﹣－․‥…
    "\u203c\u2047\u2048\u2049\ufe10\ufe13\ufe14\ufe15\ufe16\ufe19"  # ‼⁇⁈⁉︐︓︔︕︖︙
    "\ufe30\ufe35\ufe36\ufe37\ufe38\ufe47\ufe48\ufe50\ufe52\ufe54"  # ︰︵︶︷︸﹇﹈﹐﹒﹔
    "\ufe55\ufe56\ufe57\ufe59\ufe5a\ufe5b\ufe5c\ufe5f\ufe60\ufe61"  # ﹕﹖﹗﹙﹚﹛﹜﹟﹠﹡
    "\ufe62\ufe64\ufe65\ufe66\ufe68\ufe69\ufe6a\ufe6b\uff01\uff03"  # ﹢﹤﹥﹦﹨﹩﹪﹫！＃
    "\uff04\uff05\uff06\uff08\uff09\uff0a\uff0b\uff0c\uff0e\uff0f"  # ＄％＆（）＊＋，．／
    "\uff1a\uff1b\uff1c\uff1d\uff1e\uff1f\uff20\uff3b\uff3c\uff3d"  # ：；＜＝＞？＠［＼］
    "\uff3e\uff3f\uff40\uff5b\uff5c\uff5d\uff5e\u2a74\u2a75\u2a76"  # ＾＿｀｛｜｝～⩴⩵⩶
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
    "\u1d00\u1d04\u1d05\u1d07\u1d0a\u1d0b\u1d0d\u1d0f\u1d18\u1d1b"  # ᴀᴄᴅᴇᴊᴋᴍᴏᴘᴛ
    "\u1d1c\u1d20\u1d21\u1d22\u3007\u00a0\u3000"  # ᴜᴠᴡᴢ〇\u00A0\u3000
)
compatibility_to += "ACDEJKMOPTUVWZ0  "
punctuation_from = (
    "\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2032\u301d"  # ‘’‚‛“”„‟′〝
    "\u301e\u00ab\u00bb\u2039\u203a\u00ad\u2010\u2012\u2013\u2014"  # 〞«»‹›\u00AD‐‒–—
    "\u2015\u2016\u2044\u2045\u2046\u204e\u3008\u3009\u300a\u300b"  # ―‖⁄⁅⁆⁎〈〉《》
    "\u3014\u3015\u3018\u3019\u301a\u301b\u2212\u2215\u2216\u2223"  # 〔〕〘〙〚〛−∕∖∣
    "\u2225\u226a\u226b\u2985\u2986\u2022\u200b"  # ∥≪≫⦅⦆•·
)
punctuation_to = "''''\"\"\"\"'\"\"<<>><>-----||/[]*<><<>>[][][]-/\\|||<<>>(())-"
combinations_from = (
    "\u00c6\u00d0\u00d8\u00de\u00df\u00e6\u00f0\u00f8\u00fe\u0110"  # ÆÐØÞßæðøþĐ
    "\u0111\u0126\u0127\u0131\u0138\u0141\u0142\u014a\u014b\u0152"  # đĦħıĸŁłŊŋŒ
    "\u0153\u0166\u0167\u0180\u0181\u0182\u0183\u0187\u0188\u0189"  # œŦŧƀƁƂƃƇƈƉ
    "\u018a\u018b\u018c\u0190\u0191\u0192\u0193\u0195\u0196\u0197"  # ƊƋƌƐƑƒƓƕƖƗ
    "\u0198\u0199\u019a\u019d\u019e\u01a2\u01a3\u01a4\u01a5\u01ab"  # ƘƙƚƝƞƢƣƤƥƫ
    "\u01ac\u01ad\u01ae\u01b2\u01b3\u01b4\u01b5\u01b6\u01e4\u01e5"  # ƬƭƮƲƳƴƵƶǤǥ
    "\u0221\u0224\u0225\u0234\u0235\u0236\u0237\u0238\u0239\u023a"  # ȡȤȥȴȵȶȷȸȹȺ
    "\u023b\u023c\u023d\u023e\u023f\u0240\u0243\u0244\u0246\u0247"  # ȻȼȽȾȿɀɃɄɆɇ
    "\u0248\u0249\u024c\u024d\u024e\u024f\u0253\u0255\u0256\u0257"  # ɈɉɌɍɎɏɓɕɖɗ
    "\u025b\u025f\u0260\u0261\u0262\u0266\u0267\u0268\u026a\u026b"  # ɛɟɠɡɢɦɧɨɪɫ
    "\u026c\u026d\u0271\u0272\u0273\u0274\u027c\u027d\u027e\u0280"  # ɬɭɱɲɳɴɼɽɾʀ
    "\u0282\u0288\u0289\u028b\u028f\u0290\u0291\u0299\u029b\u029c"  # ʂʈʉʋʏʐʑʙʛʜ
    "\u029d\u029f\u02a0\u02a3\u02a5\u02a6\u02aa\u02ab\u1d03\u1d06"  # ʝʟʠʣʥʦʪʫᴃᴆ
    "\u1d0c\u1d6b\u1d6c\u1d6d\u1d6e\u1d6f\u1d70\u1d71\u1d72\u1d73"  # ᴌᵫᵬᵭᵮᵯᵰᵱᵲᵳ
    "\u1d74\u1d75\u1d76\u1d7a\u1d7b\u1d7d\u1d7e\u1d80\u1d81\u1d82"  # ᵴᵵᵶᵺᵻᵽᵾᶀᶁᶂ
    "\u1d83\u1d84\u1d85\u1d86\u1d87\u1d88\u1d89\u1d8a\u1d8c\u1d8d"  # ᶃᶄᶅᶆᶇᶈᶉᶊᶌᶍ
    "\u1d8e\u1d8f\u1d91\u1d92\u1d93\u1d96\u1d99\u1e9c\u1e9d\u1e9e"  # ᶎᶏᶑᶒᶓᶖᶙẜẝẞ
    "\u1efa\u1efb\u1efc\u1efd\u1efe\u1eff\u00a9\u00ae\u20a0\u20a2"  # ỺỻỼỽỾỿ©®₠₢
    "\u20a3\u20a4\u20a7\u20ba\u20b9\u211e\u3001\u3002\u00d7\u00f7"  # ₣₤₧₺₹℞、。×÷
    "\u00b7\u1e9f\u0184\u0185\u01be"  # ·ẟƄƅƾ
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
        self.assertEqual(
            util.textencoding.unicode_simplify_punctuation('\u2215\u2216', True), '__' if IS_WIN else '_\\'
        )
        self.assertEqual(
            util.textencoding.unicode_simplify_punctuation('/\\\u2215\u2216', True), '/\\__' if IS_WIN else '/\\_\\'
        )

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
        self.assertEqual(
            util.textencoding.replace_non_ascii('\u2216\u2044\u2215\uff0f/8½\\', pathsave=True, win_compat=True),
            '____/8 1_2\\',
        )

    def test_incorrect(self):
        self.assertNotEqual(util.textencoding.replace_non_ascii("Lukáš"), "Lukáš")
        self.assertNotEqual(util.textencoding.replace_non_ascii("Lukáš"), "Luk____")


if show_latin2ascii_coverage:
    # The following code set blocks are taken from:
    # http://en.wikipedia.org/wiki/Latin_script_in_Unicode
    latin_1 = "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"
    latin_a = (
        "ĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿ"
        "ŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽž"
    )
    latin_b = (
        "ƀƁƂƃƄƅƆƇƈƉƊƋƌƍƎƏƐƑƒƓƔƕƖƗƘƙƚƛƜƝƞƟƠơƢƣƤƥƦƧƨƩƪƫƬƭƮƯưƱƲƳƴƵƶƷƸƹƺƻƼƽƾƿ"
        "ǀǁǂǃǄǅǆǇǈǉǊǋǌǍǎǏǐǑǒǓǔǕǖǗǘǙǚǛǜǝǞǟǠǡǢǣǤǥǦǧǨǩǪǫǬǭǮǯǰǱǲǳǴǵǶǷǸǹǺǻǼǽǾǿ"
        "ȀȁȂȃȄȅȆȇȈȉȊȋȌȍȎȏȐȑȒȓȔȕȖȗȘșȚțȜȝȞȟȠȡȢȣȤȥȦȧȨȩȪȫȬȭȮȯȰȱȲȳȴȵȶȷȸȹȺȻȼȽȾȿ"
        "ɀɁɂɃɄɅɆɇɈɉɊɋɌɍɎɏ"
    )
    ipa_ext = "ɐɑɒɓɔɕɖɗɘəɚɛɜɝɞɟɠɡɢɣɤɥɦɧɨɩɪɫɬɭɮɯɰɱɲɳɴɵɶɷɸɹɺɻɼɽɾɿʀʁʂʃʄʅʆʇʈʉʊʋʌʍʎʏʐʑʒʓʔʕʖʗʘʙʚʛʜʝʞʟʠʡʢʣʤʥʦʧʨʩʪʫʬʭʮʯ"
    phonetic = (
        "ᴀᴁᴂᴃᴄᴅᴆᴇᴈᴉᴊᴋᴌᴍᴎᴏᴐᴑᴒᴓᴔᴕᴖᴗᴘᴙᴚᴛᴜᴝᴞᴟᴠᴡᴢᴣᴤᴥᴦᴧᴨᴩᴪᴫᴬᴭᴮᴯᴰᴱᴲᴳᴴᴵᴶᴷᴸᴹᴺᴻᴼᴽᴾᴿ"
        "ᵀᵁᵂᵃᵄᵅᵆᵇᵈᵉᵊᵋᵌᵍᵎᵏᵐᵑᵒᵓᵔᵕᵖᵗᵘᵙᵚᵛᵜᵝᵞᵟᵠᵡᵢᵣᵤᵥᵦᵧᵨᵩᵪᵫᵬᵭᵮᵯᵰᵱᵲᵳᵴᵵᵶᵷᵸᵹᵺᵻᵼᵽᵾᵿ"
        "ᶀᶁᶂᶃᶄᶅᶆᶇᶈᶉᶊᶋᶌᶍᶎᶏᶐᶑᶒᶓᶔᶕᶖᶗᶘᶙᶚᶛᶜᶝᶞᶟᶠᶡᶢᶣᶤᶥᶦᶧᶨᶩᶪᶫᶬᶭᶮᶯᶰᶱᶲᶳᶴᶵᶶᶷᶸᶹᶺᶻᶼᶽᶾᶿ"
    )
    latin_ext_add = (
        "ḀḁḂḃḄḅḆḇḈḉḊḋḌḍḎḏḐḑḒḓḔḕḖḗḘḙḚḛḜḝḞḟḠḡḢḣḤḤḦḧḨḩḪḫḬḭḮḯḰḱḲḳḴḵḶḷḸḹḺḻḼḽḾḿ"
        "ṀṁṂṃṄṅṆṇṈṉṊṋṌṍṎṏṐṑṒṓṔṕṖṗṘṙṚṛṜṝṞṟṠṡṢṣṤṥṦṧṨṩṪṫṬṭṮṯṰṱṲṳṴṵṶṷṸṹṺṻṼṽṾṿ"
        "ẀẁẂẃẄẅẆẇẈẉẊẋẌẍẎẏẐẑẒẓẔẕẖẗẘẙẚẛẜẝẞẟẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾế"
        "ỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹỺỻỼỽỾỿ"
    )
    letter_like = "℀℁ℂ℃℄℅℆ℇ℈℉ℊℋℌℍℎℏℐℑℒℓ℔ℕ№℗℘ℙℚℛℜℝ℞℟℠℡™℣ℤ℥Ω℧ℨ℩KÅℬℭ℮ℯℰℱℲℳℴℵℶℷℸℹ℺℻ℼℽℾℿ⅀⅁⅂⅃⅄ⅅⅆⅇⅈⅉ⅊⅋⅌⅍ⅎ⅏"
    enclosed = "⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛⒜⒝⒞⒟⒠⒡⒢⒣⒤⒥⒦⒧⒨⒩⒪⒫⒬⒭⒮⒯⒰⒱⒲⒳⒴⒵ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ⓪⓫⓬⓭⓮⓯"

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
