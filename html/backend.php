<?PHP

/**
 * Should contain something like
 * $sql = new SQLite3("samples.db");
 */
include('db.php');

/**
 * Query attack history for given sample.
 * The resulting list will be zero filled if no attacks were present,
 * so the resulting list should count exactly ($to - $from) / $timedelta entries.
 *
 * assert
 */
function query_history_for_sample($sample, $from, $to, $timedelta) {
	global $sql;
	
	assert($sample != "");
	assert($from % $timedelta == 0);
	assert($to   % $timedelta == 0);
	assert($timedelta > 0);
	
	$q = $sql->prepare("SELECT id FROM samples WHERE sha256 = :sha256");
	$q->bindValue(":sha256", $sample, SQLITE3_TEXT);
	$r = $q->execute();
	$id_sample = $r->fetchArray()[0];

	assert($id_sample > 0);	
	
	$q = $sql->prepare('select COUNT(conns.id), conns.date / :delta as hour from conns
	INNER JOIN conns_urls on conns_urls.id_conn = conns.id
	INNER JOIN urls on conns_urls.id_url = urls.id
	WHERE urls.sample = :id
	AND conns.date >= :from
	AND conns.date <= :to
	GROUP BY hour
	ORDER BY hour ASC');
	
	$q->bindValue(":id",    $id_sample, SQLITE3_INTEGER);
	$q->bindValue(":delta", $timedelta, SQLITE3_INTEGER);
	$q->bindValue(":from",  $from,      SQLITE3_INTEGER);
	$q->bindValue(":to",    $to,        SQLITE3_INTEGER);

	return query_history($q, $from, $to, $timedelta);
}

/**
 * Query global connectin history
 */
function query_history_new($from, $to, $timedelta) {
	global $sql;
	
	assert($from % $timedelta == 0);
	assert($to   % $timedelta == 0);
	assert($timedelta > 0);
	
	$q = $sql->prepare('select COUNT(conns.id), conns.date / :delta as hour from conns
	WHERE conns.date >= :from
	AND conns.date <= :to
	GROUP BY hour');
	
	$q->bindValue(":delta", $timedelta, SQLITE3_INTEGER);
	$q->bindValue(":from",  $from,      SQLITE3_INTEGER);
	$q->bindValue(":to",    $to,        SQLITE3_INTEGER);

	return query_history($q, $from, $to, $timedelta);
}

function query_history($q, $from, $to, $timedelta) {
	$r = $q->execute();
	
	$list = array();
	$last = $from - $timedelta;
	
	while ($row = $r->fetchArray()) {
		$date  = $row[1] * $timedelta;
		$count = $row[0];
	
		while ($last != 0 && $last + $timedelta < $date) {
			$last += $timedelta;
			array_push($list, 0);
		}
		
		array_push($list, $count);
		$last += $timedelta;
	}
	
	while ($last < $to) {
		$last += $timedelta;
		array_push($list, 0);		
	}
	
	return array(
		"from"  => $from,
		"to"    => $to,
		"delta" => $timedelta,
		"data"  => $list
	);
}

function query_history_samples() {
	global $sql;
	$timedelta = 3600 * 6;

	$q = 'select id, name, sha256 from samples';
	$result = $sql->query($q);
	$samples = Array();
	$cache   = Array();
	while ($row = $result->fetchArray()) {
		$cache[$row[0]] = $row[2];
		$samples[$row[2]] = array(
			"id"     => $row[0],
			"name"   => $row[1],
			"sha256" => $row[2],
			"data"   => array(),
			"data2"  => array()
		);
	}

	$q = 'select COUNT(conns.id), urls.sample, conns.date / ' . $timedelta . ' as hour from conns
	INNER JOIN conns_urls on conns_urls.id_conn = conns.id
	INNER JOIN urls on conns_urls.id_url = urls.id
	GROUP BY hour, urls.sample
	ORDER BY hour';

	$dates = array();
	$result = $sql->query($q);
	$firstdate   = 0;
	$currentdate = 0;
	while ($row = $result->fetchArray()) {
		$count  = $row[0];
		$id     = $row[1];
		$date   = $row[2] * $timedelta;
		$sha256 = $cache[$id];

		if ($firstdate == 0) $firstdate = $date;
		if ($currentdate != $date) { array_push($dates, $date); $currentdate = $date; }
		$samples[$sha256]["data"][$date] = $count;
	}

	foreach ($samples as $id => $sample) {
		$currentdate = $firstdate;
		foreach ($sample["data"] as $date => $count) {
			while ($date > $currentdate) {
				$currentdate += $timedelta;
				array_push($samples[$id]["data2"], 0);
			}

			$currentdate += $timedelta;
			array_push($samples[$id]["data2"], $count);
		}
		$samples[$id]["data"] = null;
	}

	return array(
		"samples" => $samples,
		"dates"   => $dates
	);
}

function query_sample_stats() {
	global $sql;
	$q = "select
	samples.name, samples.sha256, COUNT(samples.id) as count, MAX(conns.date), samples.length, samples.result
	from conns_urls
	INNER JOIN conns on conns_urls.id_conn = conns.id
	INNER JOIN urls on conns_urls.id_url = urls.id
	INNER JOIN samples on urls.sample = samples.id
	GROUP BY samples.id
	ORDER BY count DESC";

	$result = $sql->query($q);
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"count"    => $row[2],
			"name"     => $row[0],
			"sha256"   => $row[1],
			"lastseen" => $row[3],
			"length"   => $row[4],
			"result"   => $row[5]
		));
	}
	return $list;
}

function query_conn_history() {
	global $sql;
	$date = time();
	$date = $date - (($date % 3600) + 3600 * 24);
	$delta = 3600 / 2;
	$q = "select i, a, b from (
		select COUNT(id) as a, date/" . $delta . " as i from conns
		INNER JOIN conns_urls on conns_urls.id_conn = conns.id WHERE date >= " . $date . " GROUP BY i
	) INNER JOIN (
		select COUNT(id) as b, date/" . $delta . " as j from conns WHERE date >= " . $date . " GROUP BY j
	) on i=j;";
	$result = $sql->query($q);
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"date"      => $row[0] * $delta,
			"count"     => $row[2],
			"count_url" => $row[1]
		));
	}
	return $list;
}

function query_basic() {
	global $sql;
	$result = $sql->query("SELECT COUNT(id) from samples;");
	$s      = $result->fetchArray()[0];
	$result = $sql->query("SELECT COUNT(id) from urls;");
	$u      = $result->fetchArray()[0];
	$result = $sql->query("SELECT COUNT(id) from conns;");
	$c      = $result->fetchArray()[0];
	return array("samples" => $s, "connections" => $c, "urls" => $u);
}

function query_newest_samples() {
	global $sql;
	$result = $sql->query("select name, date, sha256, length from samples order by date desc limit 10");
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"name"   => $row[0],
			"date"   => $row[1],
			"sha256" => $row[2],
			"length" => $row[3]
		));
	}
	return $list;
}

function query_newest_urls() {
	global $sql;
	$result = $sql->query("select url, date from urls order by date desc limit 10");
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"url"    => $row[0],
			"date"   => $row[1]
		));
	}
	return $list;
}

function query_newest_conns() {
	global $sql;
	$result = $sql->query("select ip, date, user, pass from conns order by date desc limit 10");
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"ip"     => preg_replace("/\.\d+$/", ".xxx", $row[0]),
			"date"   => $row[1],
			"user"   => $row[2],
			"pass"   => $row[3]
		));
	}
	return $list;
}

if (!isset($_GET["cmd"])) {
    echo "var data = " . json_encode(query_sample_stats()) . ";\r\n";
    echo "var hist = " . json_encode(query_conn_history()) . ";\r\n";
    echo "var base = " . json_encode(query_basic()) . ";\r\n";
    echo "var samples = " . json_encode(query_newest_samples()) . ";\r\n";
    echo "var urls = " . json_encode(query_newest_urls()) . ";\r\n";
    echo "var conns = " . json_encode(query_newest_conns()) . ";\r\n";
} else {
	$cmd = $_GET["cmd"];
	if ($cmd == "gethistory") {
		$from   = intval($_GET["from"]);
		$to     = intval($_GET["to"]);
		$delta  = intval($_GET["delta"]);
		
		// Prevent DoS
		if (($to - $from) / $delta > 48) {
			echo json_encode("ERROR: Select smaller interval / bigger deltas");
			exit;
		}
		
		// Clamp to delta
		$to    = $to - $to % $delta + $delta;
		$from  = $from - $from % $delta;
		
		if (isset($_GET["sample"])) {
			$sample = $_GET["sample"];
			echo json_encode(query_history_for_sample($sample, $from, $to, $delta));
		} else {
			echo json_encode(query_history_new($from, $to, $delta));
		}
    }
}

?>
