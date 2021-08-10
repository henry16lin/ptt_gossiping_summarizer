import sqlite3
import pandas as pd
import numpy as np
import jieba
import jieba.analyse
import matplotlib.pyplot as plt

from gensim import corpora, models
import datetime

import text_freq_analyst
#import logging
#logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

#send email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

### functions ###

def lda_preprocess(title):
    #input query title list return title list in list with 斷詞 & 移除同意字 & 移除只出現一次的字
    
    jieba.set_dictionary('dict/dict.txt.big') # 斷詞 & get document
    stop_words = open('data/stop_words_gossiping.txt',encoding='utf8').read()
    wf = []
    for i in range(len(title)):
        wf.append(' '.join([t for t in jieba.cut(title[i], cut_all=False) if t not in stop_words]))

    texts = [ text.split(' ') for text in wf]

    # 移除只出現一次的字詞
    from collections import defaultdict
    frequency = defaultdict(int)
    for text in texts:
        for token in text:
            frequency[token] += 1
    
    texts = [[token for token in text if frequency[token] > 1]
             for text in texts]
    
    return texts


def biweek_date_generator(date):
    #return last two week date list
    full_date_obj = datetime.datetime.strptime(date, '%Y/%m/%d')
    date_list=[]
    for i in range(14):
        tmp = full_date_obj - datetime.timedelta(days=i)
        date_list.append(datetime.datetime.strftime(tmp,'%Y/%m/%d')[-5:])
        
    date_list.reverse()
    return date_list


def text_cluster(text_list,model):
    new_doc = dictionary.doc2bow(text_list)
    prob = model[new_doc]
    max_prob = max([i[1] for i in prob])
    max_prob_ind = [i[1] for i in prob].index(max_prob)
    cluster = prob[max_prob_ind][0]
    
    return cluster


def send_mail(subject,content,attach_path_list=[]):
    email_user = 'sender email address'
    email_password = 'sender password'
    email_send = 'receiver email address'
    
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = subject
    
    body = content
    msg.attach(MIMEText(body,'plain'))
    
    for i in range(len(attach_path_list)):
        part = MIMEBase('application','octet-stream')
        filename = attach_path_list[i]
        attachment = open(filename,'rb')
        part = MIMEBase('application','octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',"attachment; filename= "+filename)
        msg.attach(part)

    text = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(email_user,email_password)
    
    server.sendmail(email_user,email_send,text)
    server.quit()
    
    return True


#############################################################

date = input('input the date you want to query (yyyy/mm/dd) or pass by enter(default use yesterday): ')

try:
    date_list = biweek_date_generator(date)
except:
    today = datetime.datetime.today().strftime('%Y/%m/%d')
    yesterday_obj = datetime.datetime.strptime(today, '%Y/%m/%d')- datetime.timedelta(days=1)
    date = datetime.datetime.strftime(yesterday_obj,'%Y/%m/%d')
    print('use date: %s' %date)
    date_list = biweek_date_generator(date)



# query last two week aritcles
sql_str = " select * from gossiping_article_view where AUTHOR <>\'-\' and DATE in (\'" + '\',\''.join(date_list) + "\');"
conn = sqlite3.connect("ptt.db")
query_article_menu = pd.read_sql_query(sql_str, conn)
conn.commit()
conn.close

article_cnt = query_article_menu.shape[0]

### daily article word cloud ###
single_date_article_menu = query_article_menu[query_article_menu['DATE']==date[-5:]]
single_date_top_article_menu = single_date_article_menu[single_date_article_menu['PUSH']=='爆']

daily_article_cnt = single_date_article_menu.shape[0]
daily_top_article_cnt = single_date_top_article_menu.shape[0]


### daily freq analysis
# all article wordcloud
title = single_date_article_menu['TITLE'].tolist()
text = ','.join(title)
text_obj = text_freq_analyst.text_freq_analyst(text)
top_fq,tf_idf_result = text_obj.freq_summary(10)
wc = text_obj.word_cloud_generator()

# only top article wordcloud
top_title = single_date_top_article_menu['TITLE'].tolist()
top_text = ','.join(top_title)
top_text_obj = text_freq_analyst.text_freq_analyst(top_text)
top_top_fq,top_tf_idf_result = top_text_obj.freq_summary(10)
top_wc = top_text_obj.word_cloud_generator()


# graph wordcloud
plt.figure(figsize = (12,12))
plt.subplot(1,2,1)
plt.imshow(wc,aspect='equal')
plt.title(date+' Article Wordcloud\n (article count:'+str(daily_article_cnt)+')')
plt.axis("off")
plt.subplot(1,2,2)
plt.imshow(top_wc, aspect='equal')
plt.title(date+' Top Article Wordcloud\n (article count:'+str(daily_top_article_cnt)+')')
plt.axis("off")

plt.savefig('summary_result_fig/'+''.join(date.split('/'))+'wordcloud.jpg',bbox_inches='tight')



### recent two weeks topic model ###
if article_cnt < 1000:
    print('article count in recent two weeks <1000, check DB and input date.')
    
else:
    title = query_article_menu['TITLE'].tolist()
    texts = lda_preprocess(title)
    
    
    dictionary = corpora.Dictionary(texts) # 建立語料庫(字典) 
    #print(dictionary.token2id)
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # 創建 tfidf model
    #tfidf = models.TfidfModel(corpus)
    #corpus_tfidf = tfidf[corpus]
    
    
    #build LDA model
    num_topics=4 
    lda = models.ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=num_topics)
    
    print("LDA topics:")
    lda.print_topics(num_topics=num_topics , num_words=6)
    
    # evaluate lda model
    #from gensim.models import CoherenceModel
    #coherence_model_lda = CoherenceModel(model=lda, texts=texts, dictionary=dictionary, coherence='c_v')
    #coherence_lda = coherence_model_lda.get_coherence()
    #score_record.append(coherence_lda)
    #print('\nCoherence Score: ', coherence_lda)
    
    
    texts_dict = {}
    for i in range(len(date_list)):
        d = date_list[i]
        daily_article = query_article_menu[query_article_menu.DATE==d]
        title = daily_article['TITLE'].tolist()
        
        texts = lda_preprocess(title)
        texts_dict.update({d:texts})
    
    #count relative article count in each topic
    counter = np.zeros([len(date_list),num_topics])
    keys = list(texts_dict.keys())
    for i in range(len(keys)):
        key = keys[i]
        for t in texts_dict[key]:
            c = text_cluster(t,model=lda)
            counter[i,c]+=1
    
    ## get graph
    counter_df = pd.DataFrame(counter)
    counter_df.index = date_list
    #counter_df.plot(kind='bar',figsize=(15,4))
    
    #create legend string
    tup = lda.print_topics(num_topics=num_topics , num_words=6)
    topic=[]
    for l in tup:
        topic.append(l[1])
     
    #graph
    plt.rcParams['font.sans-serif']=['SimHei'] #for顯示中文字
    plt.figure(figsize = (12,5))
    for i in range(counter_df.shape[1]):
        plt.plot(counter_df.iloc[:,i])
        plt.xticks(rotation=90)
        plt.ylabel('Relative article count')
        plt.xlabel('Date')
        plt.title('last two weeks topic trend', fontsize=20)
        
    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width*0.65, box.height])
    plt.legend(topic, loc='center left', bbox_to_anchor=(0, -0.3))
    
    plt.savefig('summary_result_fig/'+''.join(date.split('/'))+'biweeks_topic.jpg',bbox_inches='tight')
   
'''
print('sending email...')
try:
    subject = ''.join(date.split('/'))+' ptt_gossiping summary'
    content = 'Hello!\n 最近的熱門話題第一名是"'+ top_fq[0][0]+'" 第二名是"'+ top_fq[1][0]+'" 第三名是"'+ top_fq[2][0]+'"\n 文字雲 & two-week trend 請參考附檔~'
    word_cloud_path = r'summary_result_fig/'+''.join(date.split('/'))+'wordcloud.jpg'
    trend_path = r'summary_result_fig/'+''.join(date.split('/'))+'biweeks_topic.jpg'
    send_mail(subject,content,attach_path_list=[word_cloud_path,trend_path])
    print('successfully send email!')
except:
    print('fail to send email. ignore it!')

'''

