##     Based On Python unittest framwork

实例代码如下：
```python
import xunittest
 
class TestSuit1(xunittest.TestCase):
 
  def test_1(self):
    self.assertTrue(1 > 2)
 
  def test_2(self):
    self.assertTrue( 2 > 1)

class TestSuit2(xunittest.TestCase):
 
  def test_11(self):
    self.assertTrue( 3 > 2)
 
  def test_12(self):
    self.assertTrue( 2 > 1)
 
if __name__ == '__main__':
  xunittest.main()
```
### 1. 增加交互式功能：
   如下例所示， 用命令行参数 -i 运行测试脚本会进入交互式模式。 
   交互式模式 目前支持 支持5 个命令：
* 1         help             --- 打印帮助信息（交互式命令列表）
* 2	       suite            --- 打印所有的 TestSuit 名字
* 3	       test	        --- 打印所有的 TestCase 名字以及每个 TestCase 的执行结果
*	4       run  names       --- if names in str(TestSuit) 则运行该 TestCase， 
				    even nams is not in  str(TestSuit) but names is in str(TestCase) will also this TestCase
*	5       exit             --- 退出测试脚本

lisp@bogon:~/src$python tt.py -i

```>>>>help
  test
  suite
  run
  exit
  help

>>>>suite
TestSuit1
TestSuit2

>>>>test
TestSuit1
  test_1                                             [ Not Run]                                        
  test_2                                             [ Not Run]                                        
TestSuit2
  test_11                                            [ Not Run]                                        
  test_12                                            [ Not Run]                                        

>>>>run TestSuit1
[FAILED ] 
test_1 (__main__.TestSuit1)
Traceback (most recent call last):
  File "tt.py", line 6, in test_1
    self.assertTrue(1 > 2)
AssertionError: False is not true                                 
[ PASSED ]    test_2 (__main__.TestSuit1)
----------------------------------------------------------------------
Ran 2 tests in 0.000s

[FAILED] (failures=1)

>>>>test
TestSuit1
  test_1                                        
                                                     [ FAILED ]                             
  test_2                                             [ PASSED ]                             
TestSuit2
  test_11                                            [ Not Run]                                        
  test_12                                            [ Not Run]                                        

>>>>exit
```

### 2. 美化输出测试结果
   测试结果的输出风格类似与 gtest

### 3.保留了交互式下测试用例的执行结果
