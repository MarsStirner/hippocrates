# -*- coding: utf-8 -*-


class NumToTextConverter(object):
    
    def __init__(self, value):
        self.inputVal = value
        
        self.kop = False # показывает, что сейчас идет обработка копеек
        self.intPartText = None
        self.fractPartText = None
        self.intPartDigits = None
        self.fractPartDigits = None
        
    def convert(self):
        if not self.intPartText:
            intPart, fractPart = self.parseNumber()
            self.intPartText = self.formText(intPart)
            self.kop = True
            self.fractPartText = self.formText(fractPart)
            self.kop= False

        return self
    
    
    def getRub(self):
        return u"".join(unicode(self.intPartDigits))
        
    def getRubText(self):
        return u"".join(self.intPartText)
        
    def getKop(self):
        return u"".join(unicode(self.fractPartDigits))        
    
    def getKopText(self):
        return u"".join(self.fractPartText)
       
    
    def parseNumber(self):
        
        intPart, fractPart = 0, 0 
        if float(self.inputVal).is_integer():
            intPart = int(self.inputVal)
            fractPart = 0
        else:
            intPart, fractPart = map(int, ("%.2f" % self.inputVal).split('.'))
        self.intPartDigits = intPart
        self.fractPartDigits = fractPart
        
        digits = []
        rank = 0
        rankTriad = []
        while intPart / 10 > 0:
                   
            rankTriad.insert(0, int(intPart % 10))
            intPart = intPart / 10
            rank += 1
            
            if rank == 3:
                digits.insert(0, rankTriad)
                rankTriad = []
                rank = 0
            
        if rank == 0:    
            digits.insert(0, [int(intPart)])
        else:
            rankTriad.insert(0, int(intPart))
            digits.insert(0, rankTriad)
        

        fractPart = [[fractPart/10%10, fractPart%10]]
        
#        print digits, fractPart
        
        return digits, fractPart
        
        
    def formText(self, number):
        
        if len(number) > 4:
            return u"Максимальное число: 999 000 000 000" 
        
        result = u""
        postfix = u""
        
        for rankOfClass, triad in zip(sorted(range(1, len(number)+1), reverse=True), number):
#            print rankOfClass, triad
            
            postfix = self.formPostfix(rankOfClass, triad)
            lowerTen = False
        
            for rank, num in zip(sorted(range(1, len(triad)+1), reverse=True), triad):
                if lowerTen:
                    continue
                # Обработать 10,11,12,...,19
                if (rank == 2 and num == 1):
                    val = self.getText(rankOfClass, rank, int(str(num) + str(triad[-1])))
                    lowerTen = True
                else:
                    val = self.getText(rankOfClass, rank, num)
                
                result += val + (u' ' if num != 0 else u'')
            
            
            result += postfix + (u' ' if postfix != u'' else u'')
        
        return result
    
    
    def formPostfix(self, rankOfClass, triad):
        """
        Сформировать постфикс "тысяч", "миллионов" и т.д.
        """
        numbers = triad[:]
        while len(numbers) < 3:
            numbers.insert(0, None)
        h, t, o = numbers
        
        if not h and not t and not o:
            return u""
        elif h and not t and not o:
            return self.getHundredsPostfix(rankOfClass)
        elif t == 1 and o:
            return self.getTensPostfix(rankOfClass)
        elif t and not o:
            return self.getTensPostfix(rankOfClass)
#        elif (t and o and t != 1) or (not h and not t and o):
#            return self.getOnesPostfix(rankOfClass, o)
        else:
            return self.getOnesPostfix(rankOfClass, o)
    
    
    def getOnesPostfix(self, rankOfClass, num):
        
        postfix = {
            1: u"",
            2: u"тысяч%s" % {1: u"а", 2: u"и", 3: u"и", 4: u"и", 5: u"",
                             6: u"", 7: u"", 8: u"", 9: u"", 0: u""}[num],
            3: u"миллион%s" % {1: u"", 2: u"а", 3: u"а", 4: u"а", 5: u"ов",
                               6: u"ов", 7: u"ов", 8: u"ов", 9: u"ов", 0: u""}[num],
            4: u"миллиард%s" % {1: u"", 2: u"а", 3: u"а", 4: u"а", 5: u"ов",
                                6: u"ов", 7: u"ов", 8: u"ов", 9: u"ов", 0: u""}[num]
            
            }        
        
        return postfix[rankOfClass]
    
    def getTensPostfix(self, rankOfClass):
        postfix = {
            1: u"",
            2: u"тысяч",
            3: u"миллионов",
            4: u"миллиардов"
            }
        
        return postfix[rankOfClass]
    
    def getLowTensPostfix(self):
        return u"тысяч"
    
    def getHundredsPostfix(self, rankOfClass):
        postfix = {
            1: u"",
            2: u"тысяч",
            3: u"миллионов",
            4: u"миллиардов"            
            }
        
        return postfix[rankOfClass]
                 
        
    def getText(self, rankOfClass, rank, num):
        classOnes = {
             1: self.getOnes,
             2: self.getTens,
             3: self.getHundreds
             }
        
        return classOnes[rank](num, rankOfClass)
    
        
    def getOnes(self, num, rankOfClass):
        
        ones = {
            1: u"од%s",
            2: u"дв%s",
            3: u"три%s",
            4: u"четыре%s",
            5: u"пять%s",
            6: u"шесть%s",
            7: u"семь%s",
            8: u"восемь%s",
            9: u"девять%s",
            0: u"%s"
            }
        
        rankClassOnes = {
            1: ones[num] % ({1: u"ин" if not self.kop else u"на", 2: u"а" if not self.kop else u"е",
                             3: u"", 4: u"", 5: u"", 6: u"", 7: u"", 8: u"", 9: u"", 0: u""}[num]),
            2: ones[num] % ({1: u"на", 2: u"е", 3: u"", 4: u"", 5: u"",
                            6: u"", 7: u"", 8: u"", 9: u"", 0: u""}[num]),
            3: ones[num] % ({1: u"ин", 2: u"а", 3: u"", 4: u"", 5: u"",
                            6: u"", 7: u"", 8: u"", 9: u"", 0: u""}[num]),
            4: ones[num] % ({1: u"ин", 2: u"а", 3: u"", 4: u"", 5: u"",
                            6: u"", 7: u"", 8: u"", 9: u"", 0: u""}[num]),
                         
            }
        
        
        return rankClassOnes[rankOfClass]
    
    
    def getTens(self, num, rankOfClass):
        
        tens = {
             2: u"двадцать",
             3: u"тридцать",
             4: u"сорок",
             5: u"пятьдесят",
             6: u"шестьдесят",
             7: u"семьдесят",
             8: u"восемьдесят",
             9: u"девяносто",
             0: u""
             }
        
        if num < 10:        
            return tens[num]
        else:
            return self.getLowTens(num, rankOfClass)
    
    def getLowTens(self, num, rankOfClass):
        
        lowTens = {
             10: u"десять",
             11: u"одиннадцать",
             12: u"двенадцать",
             13: u"тринадцать",
             14: u"четырнадцать",
             15: u"пятнадцать",
             16: u"шестнадцать",
             17: u"семнадцать",
             18: u"восемнадцать",
             19: u"девятнадцать"
             }
        
        return lowTens[num]
        
    
    def getHundreds(self, num, rankOfClass):
        
        hundreds = {
             1: u"сто",
             2: u"двести",
             3: u"триста",
             4: u"четыреста",
             5: u"пятьсот",
             6: u"шестьсот",
             7: u"семьсот",
             8: u"восемьсот",
             9: u"девятьсот",
             0: u""
             }
        
        return hundreds[num]
        

if __name__ == '__main__':
    
    conv = NumToTextConverter(189)
    print conv.convert().getRub(), conv.convert().getRubText(), conv.convert().getKop(), conv.convert().getKopText()
    
#    import random
#    r = random.Random()
#    for i in range(10):
#        rNum = r.randint(1, r.randint(100, 10 ** 5))
#        print rNum, " => ", NumToTextConverter(rNum).convert()

#    import timeit
#    
#    print timeit.timeit('[NumToTextConverter(i).convert() for i in range (10 ** 5)]', number=1, setup="from __main__ import NumToTextConverter")
