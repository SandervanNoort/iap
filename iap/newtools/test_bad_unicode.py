from .fix_bad_unicode import fix_bad_unicode


def test_bad_unicode():
    """Unit test"""

    checks = [
        # The input to the function must be Unicode. It's not going to try to
        # auto-decode bytes for you -- then it would just create the problems
        # it's # supposed to fix.
        ("Ãºnico", "único"),
        ('This text is fine already :þ', "This text is fine already :þ"),

        # Because these characters often come from Microsoft products, we allow
        # for the possibility that we get not just Unicode characters 128-255,
        # but also Windows's conflicting idea of what characters 128-160 are.
        ('This â€” should be an em dash', "This — should be an em dash"),

        # We might have to deal with both Windows characters and raw control
        # characters at the same time, especially when dealing with characters
        # like \x81 that have no mapping in Windows.
        ('This text is sad .â\x81”.', "This text is sad .⁔."),

        # This function even fixes multiple levels of badness:
        ('\xc3\xa0\xc2\xb2\xc2\xa0_\xc3\xa0\xc2\xb2\xc2\xa0', "ಠ_ಠ"),

        # However, it has safeguards against fixing sequences of letters and
        # punctuation that can occur in valid text:
        ('not a fan of Charlotte Brontë…”', "not a fan of Charlotte Brontë…”"),

        # Cases of genuine ambiguity can sometimes be addressed by finding
        # other characters that are not double-encoding, and expecting the
        # encoding to be consistent:
        ('AHÅ™, the new sofa from IKEA®', "AHÅ™, the new sofa from IKEA®"),

        # Finally, we handle the case where the text is in a single-byte
        # encoding that was intended as Windows-1252 all along but read as
        # Latin-1:
        ('This was never Unicode\x85', "This was never Unicode…")
        ]
    for bad, good in checks:
        if fix_bad_unicode(bad) != good:
            print("bad  ", bad)
            print("fixed", fix_bad_unicode(bad))
            print("good ", good)
    print("Done checks")
