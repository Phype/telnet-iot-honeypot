import dns.resolver
import ipaddress

def query_txt(cname):
	try:
		answer = dns.resolver.query(cname, "TXT")
		
		for rr in answer.rrset:
			if rr.strings: return rr.strings[0]
	except:
		pass

	return None

def txt_to_ipinfo(txt):
	parts = txt.split("|")
	
	return {
		"asn":     parts[0].strip(),
		"ipblock": parts[1].strip(),
		"country": parts[2].strip(),
		"reg":     parts[3].strip(),
		"updated": parts[4].strip()
	}

def txt_to_asinfo(txt):
	parts = txt.split("|")
	
	return {
		"asn":     parts[0].strip(),
		"country": parts[1].strip(),
		"reg":     parts[2].strip(),
		"updated": parts[3].strip(),
		"name":    parts[4].strip()
	}

def get_ip4_info(ip):
	oktets  = ip.split(".")
	reverse = oktets[3] + "." + oktets[2] + "." + oktets[1] + "." + oktets[0]
	
	answer = query_txt(reverse + ".origin.asn.cymru.com")
	if answer:
		return txt_to_ipinfo(answer)
	
	return None

def get_ip6_info(ip):
	ip = ipaddress.ip_address(unicode(ip))
	ip = list(ip.exploded.replace(":", ""))
	
	ip.reverse()
	
	reverse = ".".join(ip)
	
	answer = query_txt(reverse + ".origin6.asn.cymru.com")
	if answer:
		return txt_to_ipinfo(answer)
	
	return None

def get_ip_info(ip):
	is_v4 = "." in ip
	is_v6 = ":" in ip
	
	if is_v4:
		return get_ip4_info(ip)
	elif is_v6:
		return get_ip6_info(ip)
	else:
		print("Cannot parse ip " + ip)
		return None

def get_asn_info(asn):
	answer = query_txt("AS" + str(asn) + ".asn.cymru.com")
	if answer:
		return txt_to_asinfo(answer)
	
	return None

#print get_ip_info("79.220.249.125")
#print get_ip_info("2a00:1450:4001:81a::200e")
#print get_asn_info(3320)