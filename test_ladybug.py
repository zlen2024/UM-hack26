import ladybug as lb

def test_db():
    db = lb.Database(":memory:")
    conn = lb.Connection(db)
    
    try:
        conn.execute("CREATE NODE TABLE Entity(id STRING, label STRING, PRIMARY KEY(id))")
    except RuntimeError as e:
        pass
        
    try:
        conn.execute("CREATE REL TABLE RelatedTo(FROM Entity TO Entity, type STRING)")
    except RuntimeError as e:
        pass
        
    print("Schema created.")

if __name__ == "__main__":
    test_db()
