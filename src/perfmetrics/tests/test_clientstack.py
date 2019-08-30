import unittest


class Test_ClientStack(unittest.TestCase):
    @property
    def _class(self):
        from perfmetrics.clientstack import ClientStack
        return ClientStack

    def test_ctor(self):
        obj = self._class()
        self.assertIsNotNone(obj.stack)

    def test_push(self):
        obj = self._class()
        client = object()
        obj.push(client)
        self.assertEqual(obj.stack, [client])

    def test_pop_with_client(self):
        obj = self._class()
        client = object()
        obj.stack.append(client)
        got = obj.pop()
        self.assertIs(got, client)
        self.assertEqual(obj.stack, [])

    def test_pop_without_client(self):
        obj = self._class()
        got = obj.pop()
        self.assertIsNone(got)
        self.assertEqual(obj.stack, [])

    def test_get_without_client(self):
        obj = self._class()
        self.assertIsNone(obj.get())

    def test_get_with_client(self):
        obj = self._class()
        client = object()
        obj.stack.append(client)
        self.assertIs(obj.get(), client)

    def test_clear(self):
        obj = self._class()
        client = object()
        obj.stack.append(client)
        obj.clear()
        self.assertEqual(obj.stack, [])
