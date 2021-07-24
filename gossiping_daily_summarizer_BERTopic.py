import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import datetime
import sqlite3
import jieba
import jieba.analyse
import text_freq_analyst

from sklearn.feature_extraction.text import CountVectorizer
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer



def biweek_date_generator(date):
    #return last two week date list
    full_date_obj = datetime.datetime.strptime(date, '%Y/%m/%d')
    date_list=[]
    for i in range(14):
        tmp = full_date_obj - datetime.timedelta(days=i)
        date_list.append(datetime.datetime.strftime(tmp,'%Y/%m/%d')[-5:])
        
    date_list.reverse()
    return date_list

def get_yesterday():
    today = datetime.datetime.today().strftime('%Y/%m/%d')
    yesterday_obj = datetime.datetime.strptime(today, '%Y/%m/%d')- datetime.timedelta(days=1)
    date = datetime.datetime.strftime(yesterday_obj,'%Y/%m/%d')
    return date


def get_daily_wc(query_article_menu):
    ### daily freq analysis
    single_date_article_menu = query_article_menu[query_article_menu['DATE']==date[-5:]]
    single_date_top_article_menu = single_date_article_menu[single_date_article_menu['PUSH']=='爆']

    daily_article_cnt = single_date_article_menu.shape[0]
    daily_top_article_cnt = single_date_top_article_menu.shape[0]

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

    plt.savefig(os.path.join(os.getcwd(), 'summary_result_fig', ''.join(date.split('/'))+'wordcloud.jpg'), bbox_inches='tight')



def get_BERTopic_model(query_article_menu):
    ### summary recent two weeks topic model (BERTopic)
    jieba.set_dictionary('dict/dict.txt.big') # 斷詞 & get document
    with open('data/stop_words_gossiping_all.txt','r', encoding='utf8') as f:
        stop_words = f.read().splitlines()

    def tokenize_zh(text):
        words = jieba.lcut(text)
        return words

    vectorizer = CountVectorizer(tokenizer=tokenize_zh, stop_words=stop_words)
    sentence_model = SentenceTransformer("distiluse-base-multilingual-cased-v2")

    topic_model = BERTopic(embedding_model = sentence_model,
                           top_n_words=10, min_topic_size=100, verbose = True, low_memory = True,
                           vectorizer_model=vectorizer)

    corpus = query_article_menu['TITLE'].tolist()
    print('start fitting BERTopic model......')
    topics, probabilities = topic_model.fit_transform(corpus)

    return topic_model, topics




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


    

if __name__ == '__main__':


    date = input('input the date you want to query (yyyy/mm/dd) or pass by enter(default use yesterday): ')
    try:
        date_list = biweek_date_generator(date)
    except:
        date = get_yesterday()
        print('use date: %s' %date)
        date_list = biweek_date_generator(date)


    # query last two week aritcles
    sql_str = " select * from gossiping_article_view where AUTHOR <>\'-\' and DATE in (\'" + '\',\''.join(date_list) + "\');"
    conn = sqlite3.connect("ptt.db")
    query_article_menu = pd.read_sql_query(sql_str, conn)
    conn.commit()
    conn.close
    article_cnt = query_article_menu.shape[0]


    # get daily world cloud
    get_daily_wc(query_article_menu)

    # get topic
    topic_model, topics = get_BERTopic_model(query_article_menu)

    
    # summary
    topic_word = []
    for t in topics:
        topic_word.append(','.join([ i[0] for i in topic_model.get_topic(t)]))

    query_article_menu['Topic_id'] = topics
    query_article_menu['Topic_word'] = topic_word
    #query_article_menu['DATETIME'] = ['2021/'+str(i) for i in query_article_menu['DATE']]

    cnt_df = query_article_menu.groupby(['DATE','Topic_id'])['TITLE'].count().reset_index()
    cnt_df = cnt_df[cnt_df['Topic_id']>=0]
    counter_df = cnt_df.pivot(index='DATE',columns='Topic_id')


    # adjust legend
    topic_legend = []
    for t in np.unique(topics):
        topic_legend.append(','.join([ i[0] for i in topic_model.get_topic(t)]))


    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.figure(figsize = (10,6))
    for i in range(counter_df.shape[1]):
        plt.plot(counter_df.iloc[:,i], marker='o')
        plt.xticks(rotation=90)
        plt.ylabel('Relative article count')
        plt.xlabel('Date')
        plt.title('last two weeks topic trend', fontsize=20)

    t = topic_legend[1:10]
    plt.legend(t, loc='center left', bbox_to_anchor=(1.05, 0.5), fontsize='x-large')
    plt.savefig(os.path.join(os.getcwd(), 'summary_result_fig', ''.join(date.split('/'))+'biweeks_topic.jpg'), bbox_inches='tight')


    '''
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

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


