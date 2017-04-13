config = {
	"use_local_db": True,

	# Only if use_local_db == False
	# "user": "testuser",
	# "backend": "http://localhost:5000/",

	# Only if use_local_db == True, or backend
	"sql": "sqlite:///test.sqlite",
	"max_db_conn": 1,
	"sample_dir": "samples/",
}
