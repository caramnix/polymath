#!/usr/bin/env python
# coding: utf-8

# In[16]:


#@caramnix 
#orginally written on 1.21.21
#last updated on 4.28.21
#!pip install xmltodict
import os, json
import xmltodict
import pandas as pd 
import numpy as np


# In[ ]:


#uses data from https://www.govinfo.gov/bulkdata/BILLSTATUS/116/hr
#user guide for data: https://github.com/usgpo/bill-status/blob/master/BILLSTATUS-XML_User_User-Guide.md


# In[ ]:


#https://www.govinfo.gov/bulkdata/BILLSTATUS/116/hr/BILLSTATUS-116-hr.zip


# In[8]:


#I personally downloaded the raw xml files from https://www.govinfo.gov/bulkdata/BILLSTATUS/116/hr/BILLSTATUS-116-hr.zip,
#but if you wanted to you could read them in directly with something like this: 

#from io import BytesIO
#from zipfile import ZipFile
#from urllib.request import urlopen

#resp = urlopen("https://www.govinfo.gov/bulkdata/BILLSTATUS/116/hr/BILLSTATUS-116-hr.zip")
#zipfile = ZipFile(BytesIO(resp.read()))
#filename_list= zipfile.namelist()
#...


# In[18]:


#code to convert XML to JSON (because I'm picky about my data types!)
path = "BILLSTATUS-116-hr"
for filename in os.listdir(path):
    if not filename.endswith('.xml'): continue
    fullname = os.path.join(path, filename)
    with open(fullname, 'r') as f:
        xmlString = f.read()
        json_output = "BILLSTATUS-116-hr-JSON/" + filename[:-4] +".json"
    with open(json_output, 'w') as f:
        json.dump(xmltodict.parse(xmlString), f, indent=4)


# In[47]:


#code to reformat data into a managable format, pulling only the information needed from the .json
#the info being, for each bill, it's sponsor (and their last name, unique id and party), cosponsors(and their last name(s), unique id(s) and party)
#Also the type of bill and the bill number (which is saved as the key, but as a precaution also including it in the dict)

def get_dict_for_bill(bill, id_numbers):
    sponser_full_name= bill['billStatus']['bill']['sponsors']['item']['fullName']
    sponser_last_name= bill['billStatus']['bill']['sponsors']['item']['lastName']
    sponser_id= bill['billStatus']['bill']['sponsors']['item']['identifiers']["lisID"]
    id_numbers.append(int(sponser_id))
    sponser_party= bill['billStatus']['bill']['sponsors']['item']['party']
    if bill['billStatus']['bill']['policyArea'] is None: #some bills do not have a type. 
        type_bill = "not given"
    else: 
        type_bill = bill['billStatus']['bill']['policyArea']['name']
    bill_id = bill['billStatus']['bill']['billNumber']
    cospon_dict= {}
    if bill['billStatus']['bill']['cosponsors'] is None: #some bills have no cosponsors!
        cospon_dict ={} 
    else: 
        n_cospon= len(bill['billStatus']['bill']['cosponsors']['item'])

        for i in range(0,n_cospon): 
            try:
                cospon_fname = bill['billStatus']['bill']['cosponsors']['item'][i]['fullName']
                cospon_lname = bill['billStatus']['bill']['cosponsors']['item'][i]['lastName']
                cospon_party = bill['billStatus']['bill']['cosponsors']['item'][i]['party']
                cospon_id = bill['billStatus']['bill']['cosponsors']['item'][i]['identifiers']['lisID']
                id_numbers.append(int(cospon_id)) #inorder to have all the id numbers of congresspeople
                cospon_dict[i]= {"LAST NAME" : cospon_lname, "ID" : cospon_id, "PARTY" : cospon_party, "FULL NAME": cospon_fname}
            except KeyError: #see note below 
                cospon_fname = bill['billStatus']['bill']['cosponsors']['item']['fullName']
                cospon_lname = bill['billStatus']['bill']['cosponsors']['item']['lastName']
                cospon_party = bill['billStatus']['bill']['cosponsors']['item']['party']
                cospon_id = bill['billStatus']['bill']['cosponsors']['item']['identifiers']['lisID']
                id_numbers.append(int(cospon_id))
                cospon_dict[0]= {"LAST NAME" : cospon_lname, "ID" : cospon_id, "PARTY" : cospon_party,"FULL NAME": cospon_fname}
    
    #returning a dictionary of all info collected from bill
    return({"sponser": {"LAST NAME" : sponser_last_name, "ID" : sponser_id, "PARTY" : sponser_party, "FULL NAME" : sponser_full_name}, 
                    "cosponsers": cospon_dict, 
                    "type" : type_bill, 
                    "bill number": bill_id})


#note: okay, so the data is formatted weirdly, in that if there is only one cosponsor, 
#instead of sticking with how they've been formatting it they instead don't tie 0:cosponsor,
#and instead tie item: cosponsor, this catches that error and fixes it. 


# In[45]:


os.chdir("set your working directory here")


# In[48]:


#now we want to create an empty bill dictionary to store information 
#takes ~11 seconds to run
Bill_Dict={} 
id_nums = [] 
bill_nums = []

path = "BILLSTATUS-116-hr-JSON"
for filename in os.listdir(path): #go through the folder at the path given and for all the jsons, get the cleaned bill dictionary
    if not filename.endswith('.json'): continue
    fullname = os.path.join(path, filename)
    with open(fullname, 'r') as read_file:
        bill_of_interest = json.load(read_file)
        bill_id = bill_of_interest['billStatus']['bill']['billNumber']
        bill_nums.append(bill_id) #also store bill ids 
        Bill_Dict[bill_id]= get_dict_for_bill(bill_of_interest,id_nums)


# In[49]:


len(Bill_Dict) #sanity check, we passed in 9062 bills and we got that many keys in our resulting dict! 


# In[181]:


#what does Bill_Dict look like? 
Bill_Dict


# In[182]:


#save our Bill Dictionary as a json!
with open('BILLSTATUS-116-hr-JSON-fname.json', 'w') as fp:
    json.dump(Bill_Dict, fp)


# In[60]:


#sotre unique ID numbers of legislators 
u_id_nums=np.unique(id_nums)


# In[168]:


len(u_id_nums) #448. Note: this is more than the 435 house members, due to the inclusion of individuals who do not have prestreatnation, i.e Puerto Rico, DC, etc and also includes members who "replaced" individuals due to deaths


# In[51]:


#make helpful data frame from Bill_Dict that can be joined to dataframes in the futire, tying ID to Full Name
#congressperson info
leg_data= {}
for key in Bill_Dict: 
    sponser_id= Bill_Dict[str(key)]['sponser']['ID']   
    if sponser_id not in leg_data.keys():
        leg_data[int(sponser_id)]= [Bill_Dict[str(key)]['sponser']['LAST NAME'].upper(), Bill_Dict[str(key)]['sponser']['PARTY'], Bill_Dict[str(key)]['sponser']['FULL NAME'], sponser_id]
    num_cospo= len(Bill_Dict[str(key)]['cosponsers'])
    for i in range(0,num_cospo): 
        cospo_id= Bill_Dict[str(key)]['cosponsers'][i]["ID"]
        if cospo_id not in leg_data.keys():
            leg_data[int(cospo_id)]= [Bill_Dict[str(key)]['cosponsers'][i]['LAST NAME'].upper(), Bill_Dict[str(key)]['cosponsers'][i]['PARTY'],Bill_Dict[str(key)]['cosponsers'][i]['FULL NAME'], cospo_id]


# In[56]:


#what does leg_data look like?
leg_data


# In[90]:


leg_data_df= pd.DataFrame.from_dict(leg_data, orient='index')
leg_data_df.columns= ['Last Name', 'Party', 'Full Name', 'ID'] 


# In[91]:


leg_data_df


# In[66]:


#count number Cosponsors/Sponsors
#takes ~30 seconds to run
columns= ["Number Cosponsored", "Number Sponsered"]
df_ = pd.DataFrame(index=u_id_nums, columns= columns)
df_ = df_.fillna(0)

for key in Bill_Dict: 
    sponser_id= Bill_Dict[str(key)]['sponser']['ID']
    df_.loc[int(sponser_id)]["Number Sponsered"] += 1
    num_cospo= len(Bill_Dict[str(key)]['cosponsers'])
    for i in range(0,num_cospo): 
        cospo_id= Bill_Dict[str(key)]['cosponsers'][i]["ID"]
        df_.loc[int(cospo_id)]["Number Cosponsored"] += 1
   


# In[77]:


df_


# In[76]:


df_["ID"]= u_id_nums


# In[92]:


df_.ID = df_.ID.astype(int)
leg_data_df.ID= leg_data_df.ID.astype(int)


# In[93]:


joined_data= leg_data_df.merge(df_, on= "ID")
joined_data


# In[95]:


#top five sponsorers of legislation for 116th Congress
joined_data.sort_values(by='Number Sponsered', ascending=False).head()


# In[97]:


#top five people receiving the most cosponsors for 116th Congress
joined_data.sort_values(by='Number Cosponsored', ascending=False).head()


# In[67]:


#build weighted directed unipartite cosponsorship adjacency matrix, connecting cosponor to sponsor
#ex: if 91 cosponsored 99 two times that means 91,99 = 2
adj1_ = pd.DataFrame(index=u_id_nums, columns= u_id_nums)
adj1_ = adj1_.fillna(0)
for key in Bill_Dict: 
    sponser_id= Bill_Dict[str(key)]['sponser']['ID']
    num_cospo= len(Bill_Dict[str(key)]['cosponsers'])
    for i in range(0,num_cospo): 
        cospo_id= Bill_Dict[str(key)]['cosponsers'][i]["ID"]
        adj1_.loc[int(cospo_id)][int(sponser_id)] += 1


# In[68]:


adj1_ 


# In[ ]:


#save to csv! 
adj1_.to_csv("adj_matrix_cosponsorship.csv") 


# In[72]:


#number of times a legislator was cosponsored (note: this matches our above numbers)
adj1_.sum(axis=1)


# In[73]:


#number of times a legislator cosponsored others
adj1_.sum(axis=0)

