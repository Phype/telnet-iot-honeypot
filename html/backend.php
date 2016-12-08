<?PHP

$sql = new SQLite3("samples.db");

function query_sample_stats() {
	global $sql;
	$q = "select
	samples.name, samples.sha256, COUNT(samples.id), MAX(conns.date)
	from conns_urls
	INNER JOIN conns on conns_urls.id_conn = conns.id
	INNER JOIN urls on conns_urls.id_url = urls.id
	INNER JOIN samples on urls.sample = samples.id
	GROUP BY samples.id";

	$result = $sql->query($q);
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"count"    => $row[2],
			"name"     => $row[0],
			"sha256"   => $row[1],
			"lastseen" => $row[3]
		));
	}
	return $list;
}

function query_conn_history() {
	global $sql;
	$date = time();
	$date = $date - (($date % 3600) + 3600 * 24);
	$q = "select i, a, b from (
		select COUNT(id) as a, date/3600 as i from conns
		INNER JOIN conns_urls on conns_urls.id_conn = conns.id WHERE date <= " . $date . " GROUP BY i
	) INNER JOIN (
		select COUNT(id) as b, date/3600 as j from conns WHERE date <= " . $date . " GROUP BY j
	) on i=j;";
	$result = $sql->query($q);
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"date"      => $row[0] * 3600,
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
	$result = $sql->query("select name, date, sha256 from samples order by date desc limit 10");
	$list   = Array();
	while ($row = $result->fetchArray()) {
		array_push($list, array(
			"name"   => $row[0],
			"date"   => $row[1],
			"sha256" => $row[2]
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

echo "var data = " . json_encode(query_sample_stats()) . ";\r\n";
echo "var hist = " . json_encode(query_conn_history()) . ";\r\n";
echo "var base = " . json_encode(query_basic()) . ";\r\n";
echo "var samples = " . json_encode(query_newest_samples()) . ";\r\n";
echo "var urls = " . json_encode(query_newest_urls()) . ";\r\n";
echo "var conns = " . json_encode(query_newest_conns()) . ";\r\n";

?>
