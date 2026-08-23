import unittest

from src.auth.service import authenticate


class AuthenticationTest(unittest.TestCase):
    def test_nonempty_token_is_authenticated(self) -> None:
        self.assertTrue(authenticate("demo-token"))


if __name__ == "__main__":
    unittest.main()
