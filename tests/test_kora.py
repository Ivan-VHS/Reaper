import asyncio,tempfile,unittest
from pathlib import Path
from reaper.kora import runtime as k,KoraPluginManager
class KoraTests(unittest.TestCase):
 def test_manifest_has_66_functions(self):
  h=KoraPluginManager();self.assertEqual(sum(p["function_count"] for p in h.list_plugins()),66)
  self.assertEqual(len(h.list_plugins()),7);self.assertEqual(h.call("num.clamp",12,0,10),10);h.set_enabled("zdoro",False);self.assertRaises(RuntimeError,lambda:h.call("num.clamp",12,0,10))
 def test_num(self):
  self.assertEqual(k.num.clamp(12,0,10),10);self.assertEqual(k.num.clamp(x=12,min=0,max=10),10);self.assertEqual(k.num.lerp(0,10,.5),5);self.assertEqual(k.num.map_range(5,0,10,0,100),50);self.assertEqual(k.num.round_to(1.234,2),1.23);self.assertEqual(k.num.sign(-4),-1)
  self.assertTrue(k.num.approx_eq(.3,.3001,.001));self.assertEqual(k.num.gcd(12,18),6)
  self.assertEqual(k.num.lcm(4,6),12);self.assertTrue(k.num.is_prime(97));self.assertFalse(k.num.is_prime(1))
  self.assertIn(k.num.rand_int(1,2),(1,2));self.assertIsInstance(k.num.rand_normal(0,1),float)
 def test_str(self):
  self.assertEqual(k.str.slugify("Hello World"),"hello-world");self.assertEqual(k.str.slugify(text="Hello World"),"hello-world");self.assertEqual(k.str.pad_both("x",5,"-"),"--x--")
  self.assertEqual(k.str.truncate("abcdef",4),"a...");self.assertEqual(k.str.between("[x]","[","]"),"x")
  self.assertEqual(k.str.count_sub("aaaa","aa"),2);self.assertEqual(k.str.words("one, two"),["one","two"])
  self.assertEqual(k.str.to_camel("hello_world"),"helloWorld");self.assertEqual(k.str.to_snake("HTTPServer"),"http_server")
  self.assertEqual(k.str.levenshtein("kitten","sitting"),3);self.assertEqual(k.str.template("Hi {{x}}",{"x":"Kora"}),"Hi Kora")
  self.assertEqual(k.str.wrap("one two three",7),"one two\nthree")
 def test_arr(self):
  self.assertEqual(k.arr.chunk([1,2,3],2),[[1,2],[3]]);self.assertEqual(k.arr.chunk(list=[1,2],size=1),[[1],[2]]);self.assertEqual(k.arr.window([1,2,3],2),[[1,2],[2,3]])
  self.assertEqual(k.arr.compact([0,None,"",1]),[0,1]);self.assertEqual(k.arr.dedup_by([1,2,3],lambda x:x%2),[1,2])
  self.assertEqual(k.arr.group_by([1,2,3],lambda x:x%2),{1:[1,3],0:[2]})
  self.assertEqual(k.arr.partition([1,2,3],lambda x:x>1),([2,3],[1]))
  self.assertEqual(k.arr.zip_with([1,2],[3,4],lambda a,b:a+b),[4,6])
  self.assertEqual(k.arr.flatten_depth([1,[2,[3]]],1),[1,2,[3]])
  self.assertEqual(len(k.arr.sample([1,2,3],2)),2);self.assertEqual(k.arr.rotate([1,2,3],1),[3,1,2])
  self.assertEqual(k.arr.binary_search([1,3,5],3),1)
 def test_map_set_heap(self):
  self.assertEqual(k.map.get_path({"a":{"b":2}},"a.b"),2)
  self.assertEqual(k.map.set_path({"a":{"b":2}},"a.c",3),{"a":{"b":2,"c":3}})
  self.assertEqual(k.map.pick({"a":1,"b":2},["b"]),{"b":2});self.assertEqual(k.map.omit({"a":1,"b":2},["a"]),{"b":2})
  self.assertEqual(k.map.deep_merge({"a":{"b":1}},{"a":{"c":2}}),{"a":{"b":1,"c":2}})
  self.assertEqual(k.map.invert({"a":1}),{1:"a"});self.assertEqual(k.map.filter_entries({"a":1,"b":2},lambda a,b:b>1),{"b":2})
  self.assertEqual(k.set.union({1},{2}),{1,2});self.assertEqual(k.set.intersect({1,2},{2}),{2});self.assertEqual(k.set.diff({1,2},{2}),{1})
  h=[1,3,5];self.assertEqual(k.heap.push_pop(h,2),1);self.assertEqual(h,[2,3,5])
 def test_fn_err(self):
  self.assertEqual(k.fn.pipe(2,[lambda x:x+1,lambda x:x*2]),6);self.assertEqual(k.fn.compose([lambda x:x+1,lambda x:x*2])(2),5)
  self.assertEqual(k.fn.memoize(lambda x:x*x,1000)(3),9);self.assertEqual(k.fn.once(lambda:7)(),7)
  self.assertTrue(callable(k.fn.debounce(lambda:None,1)));self.assertEqual(k.fn.throttle(lambda x:x,1000)(4),4)
  self.assertEqual(k.err.try_run(lambda:2).value,2);self.assertEqual(k.err.retry(lambda:9,2,0),9)
  self.assertTrue(k.err.ensure(True,"x"));self.assertIsInstance(k.err.try_run(lambda:1/0),k.Err)
 def test_io_json_time(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"a.txt";k.io.write_atomic(p,"hello");self.assertEqual(k.io.read_text(p),"hello")
   w=k.io.watch_dir(td,lambda e:None);w.close()
  self.assertEqual(k.json.parse_safe('{"a":1}').value,{"a":1});self.assertEqual(k.json.parse_safe(raw_str='{"b":2}').value,{"b":2});self.assertIsInstance(k.json.parse_safe("{"),k.Err)
  self.assertIn('"a": 1',k.json.stringify_pretty({"a":1}));self.assertIsInstance(k.time.now_ms(),int)
  self.assertIn("2024",k.time.format_iso(1704067200000));self.assertEqual(k.sys.env_get("KORA_MISSING","fallback"),"fallback")
  self.assertIsInstance(k.sys.args(),list);self.assertEqual(k.meta.type_of(None),"null")
 def test_async(self):
  async def run():
   async def ok():return 5
   async def bad():raise ValueError("bad")
   v=await k.async_.all_settled([ok(),bad()]);self.assertEqual(v[0]["status"],"fulfilled");self.assertEqual(v[1]["status"],"rejected")
   self.assertEqual(await k.async_.race_timeout(ok(),100),5);await k.time.sleep(0)
  asyncio.run(run())
if __name__=="__main__":unittest.main()
