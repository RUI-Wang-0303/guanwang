"""启动服务后运行：.venv/Scripts/python.exe tests/test_api.py"""
import csv, io, json, unittest
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
BASE="http://127.0.0.1:8000"
def get(path):
    with urlopen(BASE+path, timeout=5) as response:
        return response.read()
class ApiTests(unittest.TestCase):
    def test_summary_consistency(self):
        data=json.loads(get("/api/dashboard"))
        self.assertEqual(len(data["pipes"]),12)
        self.assertEqual(data["summary"]["count"],12)
        self.assertEqual(data["summary"]["high_count"],4)
        self.assertEqual(sum(data["summary"]["distribution"].values()),12)
        self.assertEqual(data["summary"]["length_km"],round(sum(p["length_m"] for p in data["pipes"])/1000,2))
        self.assertEqual(data["pipes"][0]["pipe_id"],"DEMO-009")
    def test_combined_filters_and_export(self):
        query=urlencode({"risk":"高","min_diameter":1000})
        data=json.loads(get("/api/dashboard?"+query))
        rows=list(csv.reader(io.StringIO(get("/api/export?"+query).decode("utf-8-sig"))))
        self.assertEqual(data["summary"]["count"],2)
        self.assertEqual({p["pipe_id"] for p in data["pipes"]},{row[1] for row in rows[1:]})
        self.assertTrue(all(row[0]=="虚构演示数据" for row in rows[1:]))
    def test_selected_export_and_detail(self):
        rows=list(csv.reader(io.StringIO(get("/api/export?ids=DEMO-001,DEMO-003").decode("utf-8-sig"))))
        self.assertEqual(len(rows),3)
        detail=json.loads(get("/api/pipes/DEMO-003"))["pipe"]
        self.assertEqual(detail["risk_score"],63)
    def test_no_results_and_bad_input(self):
        data=json.loads(get("/api/dashboard?q=DOES-NOT-EXIST"))
        self.assertEqual(data["summary"]["count"],0)
        self.assertEqual(data["summary"]["length_km"],0)
        for path,code in [("/api/pipes/MISSING",404),("/api/dashboard?min_diameter=-1",422)]:
            with self.assertRaises(HTTPError) as error:
                get(path)
            self.assertEqual(error.exception.code,code)
if __name__=="__main__": unittest.main(verbosity=2)
