import warnings
import codecs
import re
from unidecode import unidecode


prefix_stopwords = ['the', 'a', 'der', 'die', 'das']

# LLM_ID = "Meta-Llama-3-8Bt"
# LLM_ID = "GPT4ominit"
# LLM_ID = "Meta-Llama-70Bt"
LLM_ID = "mixtral-8x7bt"

YEAR = "2025"

OUTPUT_F_10 = "./files/rankings/ranking-f-10-" + LLM_ID + "" + YEAR + ".txt"
OUTPUT_A_10 = "./files/rankings/ranking-a-10-" + LLM_ID + "" + YEAR + ".txt"
OUTPUT_F_ALL = "./files/rankings/ranking-f-all-" + LLM_ID + "" + YEAR + ".txt"
OUTPUT_A_ALL = "./files/rankings/ranking-a-all-" + LLM_ID + "" + YEAR + ".txt"


INPUTFILEPATH = "files/All_tests_LLM/prompt_output_" + LLM_ID + "" + YEAR + "_alltests_CM.csv"
print('before you run this, you need to unzip the folder entity2id.zip to retrieve potential entity names')
with warnings.catch_warnings():
	warnings.simplefilter("ignore")
	e2i_f = codecs.open("./matching/entity2id.txt", "r", "utf-8")
	e2i_f_full = codecs.open("./matching/entity2id_full.txt", "r", "utf-8")
	e2i_f_xxl = codecs.open("./matching/all_artists.txt", "r", "utf-8")
	f = codecs.open(INPUTFILEPATH, "r", "utf-8")

correct_item_counter = 0
null_item_counter = 0
toomuch_item_counter = 0
tooless_item_counter = 0

mismatch_counter = {}
mismatch_counter['artist'] = 0
mismatch_counter['festival'] = 0
match_counter = {}
match_counter['artist'] = 0
match_counter['festival'] = 0

artist_unmatched = set()
festival_unmatched = set()


def search(name, e2i, e2i_full):
	global prefix_stopwords
	regex = re.compile('[^0-9a-zA-Z ]+')
	name = normalize_entity(name)
	token = name.split(" (")
	ktoken = name.split(",")
	nameWOS = name.replace(" ","")
	variants = [
		name,
		nameWOS,
		regex.sub(' ', name),
		regex.sub('', name),
		token[0],
		"the " + name,
		"metal festival " + name,
		"festival " + name,
		name + " festival",
		name + " metal festival",
		"open air" + name,
		name + " open air"
	]

	for sw in prefix_stopwords:
		if name.startswith(sw + " "): variants.append(name[len(sw)+1:])
	if name.startswith("dj "): variants.append(name[3:])
	if len(ktoken) > 1: variants.extend([ktoken[0].strip(), ktoken[1].strip()])
	if name.endswith(" festival"): variants.append(name[0:-9])
	if name.endswith(" festival"): variants.append("festival " + name[0:-9])
	if name.endswith(" metal festival"): variants.append(name[0:-15])
	if name.endswith(" open air"): variants.append(name[0:-9])
	if name.endswith(" open air"): variants.append("open air " + name[0:-9])
	if name.startswith("the "): variants.append(name[4:])
	if name.startswith("festival "): variants.append(name[9:])
	if name.startswith("festival "): variants.append(name[9:] + " festival")
	if name.startswith("metal festival "): variants.append(name[15:])
	if name.startswith("open air "): variants.append(name[9:])
	if name.startswith("open air "): variants.append(name[9:] + " open air")
	if ":" in name: variants.append(name.replace(":", ": "))
	for variant in variants:
		if variant in e2i.keys(): return e2i[variant]
	for variant in variants:
		if variant in e2i_full.keys(): return "wrong:" + str(e2i_full[variant])
	return None

def search_artist_xxl(name, a2i):
	global prefix_stopwords
	regex = re.compile('[^0-9a-zA-Z ]+')
	name = name.lower()
	name = name.replace('_', ' ')
	name = name.replace('-', ' ')
	name = name.replace('.', '')
	nameWOS = name.replace(" ","")
	variants = [
		name,
		nameWOS,
		unidecode(name),
		regex.sub(' ', name),
		regex.sub('', name)
	]
	if name.startswith("dj "): variants.append(name[3:])
	for sw in prefix_stopwords:
		if name.startswith(sw + " "): variants.append(name[len(sw)+1:])
	for variant in variants:
		if variant in a2i.keys(): return a2i[variant]
	return None


def read_answer(answer, question):
	global correct_item_counter,tooless_item_counter,toomuch_item_counter,null_item_counter
	ranking = []
	if len(question) < 2:
		#print(str(question))
		return ranking

	expected_num = int(question[2])

	for line in answer.split("\n"):
		if re.findall("^[0-9]+\\. ", line) != [] or line.startswith("*") or line.startswith("-"):
			ranking.append(line[len(re.findall(".+? ", line)[0]):])

	if len(ranking) == 0:null_item_counter += 1
	if len(ranking) == expected_num: correct_item_counter += 1
	if len(ranking) > 0 and len(ranking) < expected_num:
		tooless_item_counter += 1
		# print(">>> too less: " + str(question))
	if len(ranking) > expected_num:
		toomuch_item_counter += 1
		# print(">>> too much: " + str(question))
		ranking = ranking[0:expected_num]
	return ranking

def split_item(item):
	mode = True # True-> question False -> answer
	string = False
	komma = False
	kommacouter = 0
	question = []
	answer = ""
	current = ""
	for c in item:
		if kommacouter > 2: mode = False
		if c == "\"":
			string = not string
			if not string:
				if not mode:
					answer = current
		elif c == ",":
			if string:
				current += ","
			else:
				kommacouter += 1
				question.append(current)
				current = ""
		else:
			if mode:current += c
			else:current += c
	return (question,read_answer(answer, question))

def write_output(items):
	global a2i, f2i
	global a2i_full, f2i_full
	global OUTPUT_A_ALL, OUTPUT_F_ALL, OUTPUT_A_10, OUTPUT_F_10, YEAR
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		file_to_wirte = codecs.open(OUTPUT_F_10, "w", "utf-8")
		file_f_10 = codecs.open(OUTPUT_F_10, "w", "utf-8")
		file_a_10 = codecs.open(OUTPUT_A_10, "w", "utf-8")
		file_f_all  = codecs.open(OUTPUT_F_ALL, "w", "utf-8")
		file_a_all  = codecs.open(OUTPUT_A_ALL, "w", "utf-8")
	current_output = ""

	for item in items:
		candidate_type = 'artist' if item[0][1] == 'festival' else 'festival'
		quantity_10_not_all = True if item[0][2] == '10' else False
		# for questionpart in item[0]:

		q_entity = item[0][0]
		q_relation = 'inv_performs_at_festival' if candidate_type == 'artist' else 'performs_at_festival'
			# 3d6bd6f inv_performs_at_festival ? 2025
			# 202d14e1-dbee-4fa1-8aeb-93bc4ba1b20b performs_at_festival ? 2025
		current_output += q_entity + "\t" + q_relation + "\t?\t" + YEAR + "\n"
		i = 0
		for answerpart in item[1]:
			id = 'ups'
			if candidate_type == 'festival': id = search(answerpart, f2i, f2i_full)
			if candidate_type == 'artist': id = search(answerpart, a2i, a2i_full)
			# print("ID = " + str(id))

			token = id
			if id == None:
				if candidate_type == 'artist':
					xxl_id = search_artist_xxl(answerpart, a2i_xxl)
					if xxl_id == None:
						token = "notfound:" + answerpart
						mismatch_counter[candidate_type] +=  1
						artist_unmatched.add(answerpart)
					else:
						token = "xxlfound:" + answerpart
						match_counter[candidate_type] +=  1
				else:
					token = "notfound:" + answerpart
					mismatch_counter[candidate_type] +=  1
					festival_unmatched.add(answerpart)
			else:
				match_counter[candidate_type] +=  1

			current_output += str(token.strip()) + "\t" + str(1.0 - 0.001 * i)+ "\t"
			i += 1
		current_output = current_output[0:-1]
		file2write2 = None
		if candidate_type == 'artist':
			file2write2 = file_a_10 if quantity_10_not_all else file_a_all
		else:
			file2write2 = file_f_10 if quantity_10_not_all else file_f_all
		file2write2.write(current_output + "\n")
		current_output = ""
	file_f_10.close()
	file_a_10.close()
	file_f_all.close()
	file_a_all.close()

def split_file(file):
	items = []
	current_item = ""
	for line in file.readlines():
		# if line.startswith("\""):
		if line.startswith("id,type,"): continue
		if ",festival," in line or ",artist," in line:
			items.append(split_item(current_item))
			current_item = line
		else:
			current_item += line
	items.append(split_item(current_item)) # do not forget the last in line
	items.pop(0) # the first one is always a bad one
	return items


def read_dictionary(e2i_f, a2i, f2i):
	for line in e2i_f:
		if len(line) > 3:
			(idn, ids) = line.split("\t");
			if ids.startswith("ARTIST:"):
				artist = ids[7:].strip()
				artist = normalize_entity(artist)
				artist_variants = create_entity_variants(artist)
				for a in artist_variants: a2i[a] = idn
			if ids.startswith("FESTIVAL:"):
				festival = ids[9:].strip()
				festival = normalize_entity(festival)
				festival_variants = create_entity_variants(festival)
				for f in festival_variants: f2i[f] = idn

def read_xxl_dictionary(e2i_f, a2i):
	regex = re.compile('[^0-9a-zA-Z ]+')
	for line in e2i_f:
		(artist, idn) = line.split("\t");
		artist = normalize_entity(artist)
		artist_variants = create_entity_variants(artist)
		for a in artist_variants: a2i[a] = idn

def normalize_entity(e):
	e = e.strip()
	e = e.replace('_', ' ')
	e = e.replace('-', ' ')
	e = e.replace('.', ' ')
	e = e.lower()
	e = unidecode(e)

	return e

def create_entity_variants(e):
	r1 = re.compile('[^0-9a-zA-Z ]+')
	r2 = re.compile('[^0-9a-zA-Z]+')
	variants = [e, r1.sub(' ', e), r2.sub('', e)]
	if "+" in e: variants.append(e.replace('+', 'and'))
	if "&" in e: variants.append(e.replace('&', 'and'))
	if e.startswith("ms "): variants.append(e[3:])
	ktoken = e.split(",")
	if len(ktoken) > 1:
		variants.append(ktoken[0].strip())
		variants.append(ktoken[1].strip())
	return variants


print(">>> reading artist and festival mappings ...")
a2i = {}
f2i = {}

a2i_full = {}
f2i_full = {}

print(">>> read gold mapping ...")
read_dictionary(e2i_f, a2i, f2i)
print(">>> read full mapping ...")
read_dictionary(e2i_f_full, a2i_full, f2i_full)

a2i_xxl = {}
print(">>> read xxl mapping ...")
read_xxl_dictionary(e2i_f_xxl, a2i_xxl)


print("len of full dictionary: " + str(len(a2i_full)))
print("len of xxl dictionary: " + str(len(a2i_xxl)))
# print(a2i.keys())

#i = 0
#for a in a2i_xxl:
#	i += 1
#	print(a)
#	if i == 50: exit()

items = split_file(f)
write_output(items)

print("--- stats of LLM files ---")
print("- correct num cands: " + str(correct_item_counter))
print("- zero cands:        " + str(null_item_counter))
print("- too many cands:    " + str(toomuch_item_counter))
print("- not enough cands:  " + str(tooless_item_counter))

print("--- stats of mappings ---")
print("- missed artists:    " + str(mismatch_counter['artist']))
print("- missed festivals:  " + str(mismatch_counter['festival']))
print("- matched artists:   " + str(match_counter['artist']))
print("- matched festivals: " + str(match_counter['festival']))
print("-------------------------")
print("")

i = 0
print("some unmatched artists:")
for x in artist_unmatched:
	print(">>> " + x + " >>> " + str(x.encode('utf-8')))
	i += 1
	if i == 10: break

i = 0
print("some unmatched festivals:")
for x in festival_unmatched:
	print(">>> " + x + " >>> " + str(x.encode('utf-8')))
	i += 1
	if i == 10: break
