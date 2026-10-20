import unittest
from tools.cognition.koronos_chat import ChatSession, OpenAICompatibleBackend
class ChatTests(unittest.TestCase):
 def test_history_bounded(self):
  c=ChatSession()
  for i in range(20): c.add("user",str(i))
  self.assertEqual(len(c.history),12)
 def test_invalid_role(self):
  with self.assertRaises(ValueError): ChatSession().add("system","bad")
 def test_empty_input(self):
  with self.assertRaises(ValueError): ChatSession().add("user"," ")
 def test_remote_http_rejected(self):
  with self.assertRaises(ValueError): OpenAICompatibleBackend("http://remote.invalid","model")
if __name__=="__main__": unittest.main()
