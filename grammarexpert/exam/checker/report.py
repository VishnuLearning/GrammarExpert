import requests
from .error import Error
import re
import nltk
from nltk.corpus import stopwords
languagecheckurl = 'http://localhost:8082/v2/check'
class Report:
    stop_words = set(stopwords.words('english'))


    def check_words_usage(self, essay, question):
        if question.keywords.strip()=='':
            return 0
        essay = essay.lower()

        phrases = [s.strip() for s in question.keywords.splitlines() if s.strip()!='']
        words = []
        for phrase in phrases:
            words += [s.strip().lower() for s in re.split(" |,|;", phrase) if s.strip()!='']

        # here we do not want the words to be in order
        numfound = 0
        for word in words:
            if word in essay:
                numfound += 1
        
        return (1 - numfound/len(words))*10

    def check_phrase_usage(self, essay, question):
        if question.keywords.strip()=='':
            return 0
        essay = essay.lower()
        phrases = [s.strip().lower() for s in question.keywords.splitlines() if s.strip()!='']
        # option1: Check exact phrase and note the start and end points and verify they are in order.
        # for now we implement this option
        # should be do in case sensitive or case insensitive mannar?
        numfound = 0
        inorder = 0
        lastloc = 0
        for phrase in phrases:
            loc = essay.find(phrase)
            if loc != -1:
                numfound += 1
                if loc >= lastloc:
                    inorder += 1
                lastloc = loc + len(phrase)
        return (1 - inorder/len(phrases))*10


        # option 2: to give some liberty to user
        # split essay into words
        # for each phrase check if those words appear continuously somewhere


    def __init__(self, essay, question):
        global languagecheckurl

        #eliminate multiple space errors
        #TODO: may be only eliminate in beginning of para and sentence
        self.essay = re.sub(' +',' ',essay)

        # replace all continuous spaces with single space

        payload = {"text":self.essay,"language":"en-US", "enabledOnly":"false"}
        response = requests.post(languagecheckurl,data = payload)
        self.errors = [Error(m) for m in response.json()['matches']]
        self.words = re.sub(r"[.,?!;():\"\']", " ", self.essay).split()
        self.wordCount = len(self.words)
        self.score = 10

        #word limit penalty
        if question.word_limit > question.min_word_count:
            r = 1 - (self.wordCount-question.min_word_count)/(question.word_limit - question.min_word_count)
        else:
            r=0
        self.wordlimitpenalty = 0
        if(self.wordCount < question.min_word_count):
            self.wordlimitpenalty = 10
        elif r > 0:
            self.wordlimitpenalty = r*question.max_word_count_penalty
        
        #average_words_per_sentences
        sentencesList = self.essay.split('.')
        self.avg_words_per_sentences = self.wordCount / len(sentencesList)

        #words_without_stop_words
        words_without_stop_words = [word for word in self.words if word not in Report.stop_words]
        
        #avergage_word_length_without_stopwords
        if len(words_without_stop_words)==0:
            self.avg_word_length_without_stopwords = 0
        else:
            self.avg_word_length_without_stopwords = sum(map(len, words_without_stop_words))/len(words_without_stop_words)
 
        desired_words_per_sentence = question.desired_mean_words_per_sentence
        min_words_per_sentence = question.desired_mean_words_per_sentence//2
        self.sentencequalitypenalty=0
        #penality regarding avg_words_per_sentences
        if self.avg_words_per_sentences < min_words_per_sentence:
            self.sentencequalitypenalty = question.max_words_per_sentence_penalty
        elif self.avg_words_per_sentences <=desired_words_per_sentence:
            self.sentencequalitypenalty = ((desired_words_per_sentence-self.avg_words_per_sentences)/desired_words_per_sentence)*question.max_words_per_sentence_penalty*2

        desired_word_length = question.desired_mean_word_length
        min_avg_word_len = question.desired_mean_word_length // 2
        self.wordqualitypenalty = 0
        if self.avg_word_length_without_stopwords < min_avg_word_len:
            self.wordqualitypenalty = question.max_word_length_penalty
        #penality regarding avg_word_length without_stop_words
        elif self.avg_word_length_without_stopwords<desired_word_length:
            self.wordqualitypenalty = ((desired_word_length-self.avg_word_length_without_stopwords)/desired_word_length)*question.max_word_length_penalty*2

        
        #spellingmistakes and grammar mistakes
        self.spellingErrorCount = len(list(filter(lambda x:x.errorType()=='spelling', self.errors)))
        self.grammarErrorCount = len(self.errors)-self.spellingErrorCount

        #TODO: check connect phrases or use words contraint
        #TODO: if keywords are there for context checking do that as well
        self.required_text_penalty  = 0
        if question.question_type == 'CP':
            self.required_text_penalty = self.check_phrase_usage(essay, question)
        elif question.question_type == 'UW':
            self.required_text_penalty = self.check_words_usage(self.words, question)

        
        #add properties for average worldlenght, sentence length, readability index etc.
        self.score -= ((self.spellingErrorCount * 0.25) + (self.grammarErrorCount * 0.25)) + self.sentencequalitypenalty + self.wordqualitypenalty + self.wordlimitpenalty + self.required_text_penalty
        if self.score < 0:
            self.score = 0
        
        
        # round'em up to 2 decimal places
        self.score = round(self.score,2)
        self.wordlimitpenalty = round(self.wordlimitpenalty, 2)
        self.wordqualitypenalty = round(self.wordqualitypenalty, 2)
        self.sentencequalitypenalty = round(self.sentencequalitypenalty, 2)
        self.required_text_penalty = round(self.required_text_penalty, 2)

        

    def reprJSON(self):
        return dict(answer=self.essay, score = self.score,errors = [e.reprJSON() for e in self.errors],
        wordCount = self.wordCount, spellingErrorCount = self.spellingErrorCount, wordlimitpenalty=self.wordlimitpenalty,
        sentencequalitypenalty = self.sentencequalitypenalty, wordqualitypenalty = self.wordqualitypenalty,
        grammarErrorCount = self.grammarErrorCount, requiredtextpenalty = self.required_text_penalty)