import textfsm

input_file = open("configs/final-inventory.txt", encoding='utf-8')
raw_text_data = input_file.read()
input_file.close()

template = open("inventory_switches.textfsm")
re_table = textfsm.TextFSM(template)
fsm_results = re_table.ParseText(raw_text_data)

outfile_name = open("Inventory.csv", "w+")
outfile = outfile_name

print(re_table.header)
for s in re_table.header:
	if s == re_table.header[-1]:
		outfile.write("%s" % s)
	else:
		outfile.write("%s," % s)
outfile.write("\n")

counter = 0
for row in fsm_results:
	print(row)
	for s in row:
		if s == row[-1]:
			outfile.write("%s" % s)
		else:
			outfile.write("%s," % s)
	outfile.write("\n")
	counter += 1
print("Write %d records" % counter)
