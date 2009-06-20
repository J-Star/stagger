# Copyright (c) 2009, Karoly Lorentey  <karoly@lorentey.hu>

import unittest

from stagger.errors import *
from stagger.specs import *
from stagger.frames import *

class SpecTestCase(unittest.TestCase):

    def testByteSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = ByteSpec("test")
        
        # spec.read
        self.assertEqual(spec.read(frame, b"\x01\x02"), (1, b"\x02"))
        self.assertEqual(spec.read(frame, b"\x01"), (1, b""))
        self.assertRaises(EOFError, spec.read, frame, b"")

        # spec.write
        self.assertEqual(spec.write(frame, 5), b"\x05")

        # spec.validate
        self.assertEqual(spec.validate(frame, 5), 5)
        self.assertRaises(ValueError, spec.validate, frame, -1)
        self.assertRaises(ValueError, spec.validate, frame, 256)
        self.assertRaises(TypeError, spec.validate, frame, "foobar")

    def testIntegerSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = IntegerSpec("test", 2)
        
        # spec.read
        self.assertEqual(spec.read(frame, b"\x01\x02\x03\x04"), (258, b"\x03\x04"))
        self.assertEqual(spec.read(frame, b"\x01\x02"), (258, b""))
        self.assertRaises(EOFError, spec.read, frame, b"")
        self.assertRaises(EOFError, spec.read, frame, b"\x01")

        # spec.write
        self.assertEqual(spec.write(frame, 1), b"\x00\x01")
        self.assertEqual(spec.write(frame, 258), b"\x01\x02")

        # spec.validate
        self.assertEqual(spec.validate(frame, 5), 5)
        self.assertRaises(ValueError, spec.validate, frame, -1)
        self.assertRaises(ValueError, spec.validate, frame, 65537)
        self.assertRaises(ValueError, spec.validate, frame, 65536)
        self.assertRaises(TypeError, spec.validate, frame, "foobar")

    def testSignedIntegerSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = SignedIntegerSpec("test", 2)
        
        # spec.read
        self.assertEqual(spec.read(frame, b"\x01\x02\x03\x04"), (258, b"\x03\x04"))
        self.assertEqual(spec.read(frame, b"\x01\x02"), (258, b""))
        self.assertEqual(spec.read(frame, b"\xFF\xFF"), (-1, b""))
        self.assertEqual(spec.read(frame, b"\x80\x00"), (-32768, b""))
        self.assertRaises(EOFError, spec.read, frame, b"")
        self.assertRaises(EOFError, spec.read, frame, b"\x01")

        # spec.write
        self.assertEqual(spec.write(frame, 1), b"\x00\x01")
        self.assertEqual(spec.write(frame, 258), b"\x01\x02")
        self.assertEqual(spec.write(frame, -1), b"\xFF\xFF")
        self.assertEqual(spec.write(frame, -2), b"\xFF\xFE")
        self.assertEqual(spec.write(frame, -32768), b"\x80\x00")

        # spec.validate
        self.assertEqual(spec.validate(frame, 5), 5)
        self.assertEqual(spec.validate(frame, -1), -1)
        self.assertEqual(spec.validate(frame, 32767), 32767)
        self.assertEqual(spec.validate(frame, -32768), -32768)
        self.assertRaises(ValueError, spec.validate, frame, 32768)
        self.assertRaises(ValueError, spec.validate, frame, -32769)
        self.assertRaises(TypeError, spec.validate, frame, "foobar")

    def testVarIntSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = VarIntSpec("test")
        
        # spec.read
        self.assertEqual(spec.read(frame, b"\x10\x01\x02\x03"), (258, b"\x03"))
        self.assertEqual(spec.read(frame, b"\x10\xFF\xFF"), (65535, b""))
        self.assertEqual(spec.read(frame, b"\x08\x05"), (5, b""))
        self.assertEqual(spec.read(frame, b"\x01\x05"), (5, b""))
        self.assertEqual(spec.read(frame, b"\x02\x05"), (5, b""))
        self.assertRaises(EOFError, spec.read, frame, b"")
        self.assertRaises(EOFError, spec.read, frame, b"\x08")
        self.assertRaises(EOFError, spec.read, frame, b"\x10\x01")

        # spec.write
        self.assertEqual(spec.write(frame, 0), b"\x20\x00\x00\x00\x00")
        self.assertEqual(spec.write(frame, 1), b"\x20\x00\x00\x00\x01")
        self.assertEqual(spec.write(frame, 258), b"\x20\x00\x00\x01\x02")
        self.assertEqual(spec.write(frame, 1 << 32), b"\x40\x00\x00\x00\x01\x00\x00\x00\x00")

        # spec.validate
        self.assertEqual(spec.validate(frame, 5), 5)
        self.assertEqual(spec.validate(frame, 1 << 32), 1 << 32)
        self.assertEqual(spec.validate(frame, 1 << 64 + 3), 1 << 64 + 3)
        
        self.assertRaises(ValueError, spec.validate, frame, -32769)
        self.assertRaises(TypeError, spec.validate, frame, "foobar")

    def testBinaryDataSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = BinaryDataSpec("test")
        
        # spec.read
        self.assertEqual(spec.read(frame, b""), (b"", b""))
        self.assertEqual(spec.read(frame, b"\x01"), (b"\x01", b""))
        self.assertEqual(spec.read(frame, bytes(range(100))), (bytes(range(100)), b""))

        # spec.write
        self.assertEqual(spec.write(frame, b""), b"")
        self.assertEqual(spec.write(frame, b"\x01\x02"), b"\x01\x02")
        self.assertEqual(spec.write(frame, bytes(range(100))), bytes(range(100)))

        # spec.validate
        self.assertEqual(spec.validate(frame, b""), b"")
        self.assertEqual(spec.validate(frame, b"12"), b"12")
        self.assertRaises(TypeError, spec.validate, frame, 1)
        self.assertRaises(TypeError, spec.validate, frame, [1, 2])
        self.assertRaises(TypeError, spec.validate, frame, "foobar")

    def testSimpleStringSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = SimpleStringSpec("test", 6)
        
        # spec.read
        self.assertEqual(spec.read(frame, b"Foobar"), ("Foobar", b""))
        self.assertEqual(spec.read(frame, b"Foobarbaz"), ("Foobar", b"baz"))
        self.assertEqual(spec.read(frame, b"F\xF6\xF8b\xE1r"), ("F\u00F6\u00F8b\u00E1r", b""))

        # spec.write
        self.assertEqual(spec.write(frame, "Foobar"), b"Foobar")
        self.assertEqual(spec.write(frame, "F\u00F6\u00F8b\u00E1r"), b"F\xF6\xF8b\xE1r")

        # spec.validate
        self.assertEqual(spec.validate(frame, "Foobar"), "Foobar")
        self.assertEqual(spec.validate(frame, "F\u00F6\u00F8b\u00E1r"), "F\u00F6\u00F8b\u00E1r")
        self.assertRaises(TypeError, spec.validate, frame, 1)
        self.assertRaises(TypeError, spec.validate, frame, [1, 2])
        self.assertRaises(TypeError, spec.validate, frame, b"foobar")
        self.assertRaises(UnicodeEncodeError, spec.validate, frame, "\u2011oobar")

    def nullstringhelper(self, frame, spec):
        # spec.read
        self.assertEqual(spec.read(frame, b""), ("", b""))
        self.assertEqual(spec.read(frame, b"\x00"), ("", b""))
        self.assertEqual(spec.read(frame, b"Foo"), ("Foo", b""))
        self.assertEqual(spec.read(frame, b"Foo\x00"), ("Foo", b""))
        self.assertEqual(spec.read(frame, b"Foo\x00Bar"), ("Foo", b"Bar"))
        self.assertEqual(spec.read(frame, b"F\xF6\xF8b\xE1r\x00Bar"), ("F\u00F6\u00F8b\u00E1r", b"Bar"))

        # spec.write
        self.assertEqual(spec.write(frame, "Foobar"), b"Foobar\x00")
        self.assertEqual(spec.write(frame, "F\u00F6\u00F8b\u00E1r"), b"F\xF6\xF8b\xE1r\x00")

        # spec.validate
        self.assertEqual(spec.validate(frame, "Foobar"), "Foobar")
        self.assertEqual(spec.validate(frame, "F\u00F6\u00F8b\u00E1r"), "F\u00F6\u00F8b\u00E1r")
        self.assertRaises(TypeError, spec.validate, frame, 1)
        self.assertRaises(TypeError, spec.validate, frame, [1, 2])
        self.assertRaises(TypeError, spec.validate, frame, b"foobar")
        self.assertRaises(UnicodeEncodeError, spec.validate, frame, "\u2011oobar")
        
    def testNullTerminatedStringSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = NullTerminatedStringSpec("test")

        self.nullstringhelper(frame, spec)

        self.assertEqual(spec.read(frame, b"\x00\x00"), ("", b"\x00"))
        self.assertEqual(spec.read(frame, b"Foo\x00\x00"), ("Foo", b"\x00"))
        self.assertEqual(spec.read(frame, b"Foo\x00Bar\x00"), ("Foo", b"Bar\x00"))
        self.assertEqual(spec.read(frame, b"\x00Bar\x00"), ("", b"Bar\x00"))

    def testURLStringSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = URLStringSpec("test")

        self.nullstringhelper(frame, spec)

        self.assertEqual(spec.read(frame, b"\x00\x00"), ("", b""))
        self.assertEqual(spec.read(frame, b"Foo\x00\x00"), ("Foo", b"\x00"))
        self.assertEqual(spec.read(frame, b"Foo\x00Bar\x00"), ("Foo", b"Bar\x00"))
        self.assertEqual(spec.read(frame, b"\x00Bar\x00"), ("Bar", b""))
    
    def testEncodingSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = EncodingSpec("test")
        
        # spec.read
        self.assertEqual(spec.read(frame, b"\x01\x02"), (1, b"\x02"))
        self.assertEqual(spec.read(frame, b"\x01"), (1, b""))
        self.assertRaises(EOFError, spec.read, frame, b"")
        self.assertRaises(FrameError, spec.read, frame, b"\x04")

        # spec.write
        self.assertEqual(spec.write(frame, 3), b"\x03")

        # spec.validate
        self.assertEqual(spec.validate(frame, 3), 3)
        self.assertEqual(spec.validate(frame, "utf8"), 3)
        self.assertEqual(spec.validate(frame, "UTF-8"), 3)
        self.assertRaises(ValueError, spec.validate, frame, -1)
        self.assertRaises(ValueError, spec.validate, frame, 4)
        self.assertRaises(TypeError, spec.validate, frame, "foobar")

    def testEncodedStringSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = EncodedStringSpec("test")

        # spec.read
        self.assertEqual(spec.read(frame, b""), ("", b""))
        self.assertEqual(spec.read(frame, b"Foo"), ("Foo", b""))
        self.assertEqual(spec.read(frame, b"Foobar\x00"), ("Foobar", b""))
        self.assertEqual(spec.read(frame, b"\x00Foobar"), ("", b"Foobar"))
        frame.encoding = "utf-16-be"
        self.assertEqual(spec.read(frame, b"\x00F\x00o\x00o"), ("Foo", b""))
        self.assertEqual(spec.read(frame, b"\x00F\x00o\x00o\x00\x00"), ("Foo", b""))
        self.assertEqual(spec.read(frame, b"\x00F\x01\x00\x00a"), ("F\u0100a", b""))

        # Broken terminal character
        self.assertRaises(EOFError, spec.read, frame, b"\x00F\x00")

        # spec.write
        frame.encoding = "iso-8859-1"
        self.assertEqual(spec.write(frame, ""), b"\x00")
        self.assertEqual(spec.write(frame, "Foobar"), b"Foobar\x00") 
        self.assertRaises(UnicodeEncodeError, spec.write, frame, "\u0100")
        frame.encoding = "utf-8"
        self.assertEqual(spec.write(frame, ""), b"\x00")
        self.assertEqual(spec.write(frame, "Foobar"), b"Foobar\x00")
        self.assertEqual(spec.write(frame, "\u0100"), b"\xC4\x80\x00")
        frame.encoding = "utf-16"
        self.assertTrue(spec.write(frame, "") in [b"\xFE\xFF\x00\x00", b"\xFF\xFE\x00\x00"])
        self.assertTrue(spec.write(frame, "B") in [b"\xFE\xFF\x00B\x00\x00", b"\xFF\xFEB\x00\x00\x00"])
        frame.encoding = "utf-16-be"
        self.assertEqual(spec.write(frame, ""), b"\x00\x00")
        self.assertEqual(spec.write(frame, "B"), b"\x00B\x00\x00")
        
        # spec.validate
        for encoding in ["iso-8859-1", "utf-16", "utf-16-be", "utf-8"]:
            frame.encoding = encoding
            self.assertEqual(spec.validate(frame, ""), "")
            self.assertEqual(spec.validate(frame, "foo"), "foo")
            self.assertEqual(spec.validate(frame, "\xF0"), "\xF0")
            self.assertRaises(TypeError, spec.validate, frame, -1)
            self.assertRaises(TypeError, spec.validate, frame, 4)
            self.assertRaises(TypeError, spec.validate, frame, 3.4)
        frame.encoding = "iso-8859-1"
        self.assertRaises(UnicodeEncodeError, spec.validate, frame, "\u0100")

    def testSequenceSpec(self):
        frame = object()
        spec = SequenceSpec("test", NullTerminatedStringSpec("text"))

        # spec.read
        self.assertEqual(spec.read(frame, b""), ([], b""))
        self.assertEqual(spec.read(frame, b"Foo"), (["Foo"], b""))
        self.assertEqual(spec.read(frame, b"Foo\x00Bar\x00"), (["Foo", "Bar"], b""))
        self.assertEqual(spec.read(frame, b"\x00Foobar"), (["", "Foobar"], b""))
        self.assertEqual(spec.read(frame, b"\x00" * 10), ([""] * 10, b""))

        # spec.write
        self.assertEqual(spec.write(frame, ""), b"\x00")
        self.assertEqual(spec.write(frame, "Foobar"), b"Foobar\x00") 
        self.assertEqual(spec.write(frame, [""] * 10), b"\x00" * 10)
        self.assertEqual(spec.write(frame, ["Foo"] * 10), b"Foo\x00" * 10)
        
        # spec.validate
        self.assertEqual(spec.validate(frame, ""), [""])
        self.assertEqual(spec.validate(frame, [""]), [""])
        self.assertEqual(spec.validate(frame, "foo"), ["foo"])
        self.assertEqual(spec.validate(frame, ["foo"]), ["foo"])
        self.assertEqual(spec.validate(frame, ["foo"] * 10), ["foo"] * 10)
        self.assertRaises(TypeError, spec.validate, frame, -1)
        self.assertRaises(TypeError, spec.validate, frame, 4)
        self.assertRaises(TypeError, spec.validate, frame, 3.4)

    def testMultiSpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = MultiSpec("test", 
                         NullTerminatedStringSpec("text"), 
                         IntegerSpec("value", 2))

        # spec.read
        self.assertEqual(spec.read(frame, b""), ([], b""))
        self.assertRaises(EOFError, spec.read, frame, b"Foo")
        self.assertEqual(spec.read(frame, b"Foo\x00\x01\x02"), 
                         ([("Foo", 258)], b""))
        self.assertEqual(spec.read(frame, b"Foo\x00\x01\x02Bar\x00\x02\x03"), 
                         ([("Foo", 258), ("Bar", 515)], b""))
        self.assertEqual(spec.read(frame, b"\x00\x01\x02Foobar\x00\x02\x03"), 
                         ([("", 258), ("Foobar", 515)], b""))

        # spec.write
        self.assertEqual(spec.write(frame, []), b"")
        self.assertEqual(spec.write(frame, [("Foo", 1)]), b"Foo\x00\x00\x01") 
        self.assertEqual(spec.write(frame, [("Foo", 1), ("Bar", 2)]), 
                         b"Foo\x00\x00\x01Bar\x00\x00\x02")
        self.assertEqual(spec.write(frame, [("Foo", 1), ("Bar", 2)] * 10), 
                         b"Foo\x00\x00\x01Bar\x00\x00\x02" * 10)
        
        # spec.validate
        self.assertEqual(spec.validate(frame, []), [])
        self.assertEqual(spec.validate(frame, [["Foo", 1]] * 10), [("Foo", 1)] * 10)
        self.assertRaises(TypeError, spec.validate, frame, 1)
        self.assertRaises(TypeError, spec.validate, frame, "foo")
        self.assertRaises(ValueError, spec.validate, frame, [["Foo", 2, 2]])
        
    def testASPISpec(self):
        frame = TextFrame(frameid="TEST", encoding=3)
        spec = ASPISpec("test")
        # spec.read
        frame.b = 1
        frame.N = 5
        self.assertEqual(spec.read(frame, b"\x01\x02\x03\x04\x05\x06\x07"),
                         ([1, 2, 3, 4, 5], b"\x06\x07"))
        self.assertRaises(EOFError, spec.read, frame, b"\x01\x02")
        frame.b = 2
        frame.N = 2
        self.assertEqual(spec.read(frame, b"\x01\x02\x03\x04\x05\x06\x07"), 
                         ([258, 772], b"\x05\x06\x07"))
        self.assertRaises(EOFError, spec.read, frame, b"\x01\x02\x03")

        # spec.write
        frame.b = 1
        frame.N = 4
        self.assertEqual(spec.write(frame, [1, 2, 3, 4]), b"\x01\x02\x03\x04")
        frame.b = 2
        self.assertEqual(spec.write(frame, [1, 2, 3, 4]), b"\x00\x01\x00\x02\x00\x03\x00\x04")
        
        # spec.validate
        frame.N = 4
        frame.b = 1
        self.assertRaises(ValueError, spec.validate, frame, [])
        self.assertEqual(spec.validate(frame, [1, 2, 3, 4]), [1, 2, 3, 4])
        self.assertEqual(spec.validate(frame, b"\x01\x02\x03\x04"), [1, 2, 3, 4])
        self.assertRaises(TypeError, spec.validate, frame, 1)
        self.assertRaises(TypeError, spec.validate, frame, "1234")
        self.assertRaises(ValueError, spec.validate, frame, [1, 2, 3])
        self.assertRaises(ValueError, spec.validate, frame, [1, 2, 3, 4, 5])
        
suite = unittest.TestLoader().loadTestsFromTestCase(SpecTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="suite")