import ladybug as lb
db1 = lb.Database("test.lbug")
try:
    db2 = lb.Database("test.lbug")
    print("Success")
except Exception as e:
    print(f"Error: {e}")
