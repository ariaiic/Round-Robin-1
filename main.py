import json
from http.server import BaseHTTPRequestHandler, HTTPServer


def get_arrival(p):
    return p["arrival"]


def round_robin(quantum, procs):
    procs.sort(key=get_arrival)
    for p in procs:
        p["left"] = p["burst"]      
        p["first"] = None           
        p["added"] = False          

    time = 0
    queue = []
    gantt = []
    finished = 0
    current = None                  

    while finished < len(procs):
        for p in procs:             
            if p["arrival"] <= time and not p["added"]:
                queue.append(p)
                p["added"] = True

        if current and current["left"] > 0:
            queue.append(current)   

        if not queue:               
            time += 1
            continue

        current = queue.pop(0)
        if current["first"] is None:
            current["first"] = time
        run = min(quantum, current["left"])
        gantt.append({"pid": current["pid"], "start": time, "end": time + run})
        time += run
        current["left"] -= run
        if current["left"] == 0:
            current["end"] = time
            finished += 1

    metrics = []
    total = {"turnaround": 0, "waiting": 0, "response": 0}
    for p in procs:
        t = p["end"] - p["arrival"]
        w = t - p["burst"]
        r = p["first"] - p["arrival"]
        metrics.append({"pid": p["pid"], "arrival": p["arrival"], "burst": p["burst"],
                        "first": p["first"], "completion": p["end"],
                        "turnaround": t, "waiting": w, "response": r})
        total["turnaround"] += t
        total["waiting"] += w
        total["response"] += r

    avg = {}
    for name in total:
        avg[name] = round(total[name] / len(procs), 2)
    return {"gantt": gantt, "metrics": metrics, "avg": avg}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):               
        page = open("index.html", "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):              
        size = int(self.headers["Content-Length"])
        data = json.loads(self.rfile.read(size))
        result = round_robin(data["quantum"], data["processes"])
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())


print("Сайт: http://127.0.0.1:8001")
HTTPServer(("127.0.0.1", 8001), Handler).serve_forever()
