import requests
import lxml.html as lh
import pandas as pd


BASE_URL='https://www.fantacalcio-online.com/it/asta-fantacalcio-stima-prezzi'
#Create a handle, page, to handle the contents of the website
page = requests.get(BASE_URL, timeout=10)
#Store the contents of the website under doc
doc = lh.fromstring(page.content)
#Parse data that are stored between <tr>..</tr> of HTML
tr_elements = doc.xpath('//tr')

#Create empty list
col=[]
#For each row, store each first element (header) and an empty list
for t in tr_elements[2]:
    name=t.text_content()
    col.append((name,[]))

#Since out first row is the header, data is stored on the second row onwards
for j in range(4,len(tr_elements)):
    #T is our j'th row
    T=tr_elements[j]

    #Iterate through each element of the row
    for i, t in enumerate(T.iterchildren()):
        data=t.text_content()
        #Check if row is the first
        if i>0:
        #Convert any numerical value to integers
            try:
                data=float(data)
            except ValueError:
                data=data.strip()
        #Append the data to the empty list of the i'th column
        col[i][1].append(data)


result={title:column for (title,column) in col}
df=pd.DataFrame(result)
df.to_excel('price_fanta.xlsx', index=False)
