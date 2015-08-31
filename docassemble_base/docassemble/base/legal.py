from docassemble.base.core import DAObject
from docassemble.base.util import comma_and_list, get_language, set_language, word, words, comma_list, ordinal, need, nice_number, possessify, your, her, his, do_you, does_a_b, verb_past, verb_present, noun_plural, underscore_to_space, space_to_underscore, force_ask, period_list, currency, indefinite_article, today, remove, nodoublequote, capitalize
from docassemble.base.filter import file_finder, url_finder, mail_variable
#from docassemble.base.logger import logmessage
from datetime import date
import inspect
import re
import sys
from decimal import Decimal

class Court(DAObject):
    def __str__(self):
        return(self.name)
    def __repr__(self):
        return(self.name)

class Case(DAObject):
    def init(self):
        self.initializeAttribute(name='plaintiff', objectType=PartyList)
        self.initializeAttribute(name='defendant', objectType=PartyList)
        self.firstParty = self.plaintiff
        self.secondParty = self.defendant
        self.case_id = ""
        return super(Case, self).init()
    def parties(self):
        output_list = list()
        for partyname in ['plaintiff', 'defendant', 'petitioner', 'respondent']:
            if hasattr(self, partyname) and getattr(self, partyname).gathered:
                for indiv in getattr(self, partyname):
                    if indiv not in output_list:
                        output_list.append(indiv)
        return(output_list)

class Jurisdiction(DAObject):
    pass

class Document(DAObject):
    pass

class LegalFiling(Document):
    def init(self):
        self.title = None
        return super(Document, self).init()
    def caption(self):
        self.case.firstParty.gathered
        self.case.secondParty.gathered
        output = ""
        output += "[BOLDCENTER] " + (word("In the") + " " + self.case.court.name).upper() + "\n\n"
        output += "[BEGIN_CAPTION]"
        output += comma_and_list(self.case.firstParty.elements, comma_string=",[NEWLINE]", and_string=word('and'), before_and=" ", after_and='[NEWLINE]') + ",[NEWLINE]"
        output += "[TAB][TAB]" + self.case.firstParty.as_noun().capitalize() + "[NEWLINE] "
        output += "[SKIPLINE][TAB]" + word('v.') + " [NEWLINE][SKIPLINE] "
        output += comma_and_list(self.case.secondParty.elements, comma_string=",[NEWLINE]", and_string=word('and'), before_and=" ", after_and='[NEWLINE]') + ",[NEWLINE]"
        output += "[TAB][TAB]" + self.case.secondParty.as_noun().capitalize()
        output += "[VERTICAL_LINE]"
        output += word('Case No.') + " " + self.case.case_id
        output += "[END_CAPTION]\n\n"
        if self.title is not None:
            output += "[BOLDCENTER] " + self.title.upper() + "\n"
        return(output)

# class LegalAction(DAObject):
#     def init(self):
#         self.court = Court('court')

class Name(DAObject):
    def full(self):
        return(self.text)
    def __str__(self):
        return(self.full())
    def __repr__(self):
        return(self.full())

class IndividualName(Name):
    def full(self):
        return(self.first + " " + self.last)
    def firstlast(self):
        return(self.first + " " + self.last)
    def lastfirst(self):
        return(self.last + ", " + self.first)
    def __str__(self):
        return(self.full())
    def __repr__(self):
        return(self.full())

class Address(DAObject):
    def __str__(self):
        return(self.block())
    def block(self):
        output = '| ' + self.address + "\n"
        if hasattr(self, 'unit') and self.unit:
            output += '| ' + self.unit + "\n"
        output += '| ' + self.city + ", " + self.state + " " + self.zip
        return(output)
    pass

class Person(DAObject):
    def init(self):
        self.initializeAttribute(name='name', objectType=Name)
        self.initializeAttribute(name='address', objectType=Address)
        #logmessage("Got to this place\n")
        self.roles = set()
        return super(Person, self).init()
    def __setattr__(self, attrname, value):
        if attrname == 'name' and type(value) == str:
            self.name.text = value
        else:
            self.__dict__[attrname] = value
    def __str__(self):
        return self.name.full()
    def address_block(self):
        return('| ' + self.name.full() + "\n" + self.address.block())
    def email_address(self, include_name=None):
        if include_name is True or (hasattr(self.name, 'first') and include_name is not False):
            return('"' + nodoublequote(self.name) + '" <' + str(self.email) + '>')
        return(str(self.email))
    def age(self):
        if (hasattr(self, 'age_in_years')):
            return self.age_in_years
        today = date.today()
        born = self.birthdate
        try: 
            birthday = born.replace(year=today.year)
        except ValueError: # raised when birth date is February 29 and the current year is not a leap year
            birthday = born.replace(year=today.year, month=born.month+1, day=1)
        if birthday > today:
            return today.year - born.year - 1
        else:
            return today.year - born.year
    def do_question(self, the_verb, **kwargs):
        #logmessage("do_question kwargs are " + str(kwargs) + "\n")
        if self.instanceName == 'user':
            return(do_you(the_verb, **kwargs))
        else:
            return(does_a_b(self.name, the_verb, **kwargs))
    def does_verb(self, the_verb, **kwargs):
        #logmessage("does_verb kwargs are " + str(kwargs) + "\n")
        if self.instanceName == 'user':
            tense = 1
        else:
            tense = 3
        if ('past' in kwargs and kwargs['past'] == True) or ('present' in kwargs and kwargs['present'] == False):
            return verb_past(the_verb, person=tense)
        else:
            return verb_present(the_verb, person=tense)
    def did_verb(self, the_verb, **kwargs):
        if self.instanceName == 'user':
            tense = 1
        else:
            tense = 3
        return verb_past(the_verb, person=tense)

class Individual(Person):
    def init(self):
        self.initializeAttribute(name='name', objectType=IndividualName)
        self.initializeAttribute(name='child', objectType=ChildList)
        self.initializeAttribute(name='income', objectType=Income)
        self.initializeAttribute(name='asset', objectType=Asset)
        self.initializeAttribute(name='expense', objectType=Expense)
        #logmessage("Got to this here place\n")
        return super(Individual, self).init()
    def possessive(self, target):
        if self.instanceName == 'user':
            return your(target)
        else:
            return possessify(self.name, target)
    def do_verb(self, verb):
        if self.instanceName == 'user':
            return ""
        else:
            return possessify(self.name, target)
    def salutation(self):
        if self.gender == 'female':
            return('Ms.')
        else:
            return('Mr.')
    def pronoun_possessive(self, target):
        if self.instanceName == 'user':
            return your(target)
        if self.gender == 'female':
            return her(target)
        else:
            return his(target)
    def pronoun(self):
        if self.instanceName == 'user':
            return word('you')
        if self.gender == 'female':
            return word('her')
        else:
            return word('him')

class DAList(DAObject):
    def init(self):
        self.elements = list()
        self.gathering = False
        return super(DAList, self).init()
    def add(self, element):
        self.elements.append(element)
    def addObject(self, objectFunction):
        newobject = objectFunction(self.instanceName + '[' + str(len(self.elements)) + ']')
        self.elements.append(newobject)
        return newobject
    def first(self):
        return self.elements[0]
    def last(self):
        return self.elements[-1]
    def does_verb(self, the_verb, **kwargs):
        if not self.gathering:
            self.gathered
        if len(self.elements) > 1:
            tense = 'plural'
        else:
            tense = 3
        if ('past' in kwargs and kwargs['past'] == True) or ('present' in kwargs and kwargs['present'] == False):
            return verb_past(the_verb, person=tense)
        else:
            return verb_present(the_verb, person=tense)
    def did_verb(self, the_verb, **kwargs):
        if not self.gathering:
            self.gathered
        if len(self.elements) > 1:
            tense = 'plural'
        else:
            tense = 3
        return verb_past(the_verb, person=tense)
    def as_singular_noun(self, *pargs):
        if not self.gathering:
            self.gathered
        if len(pargs) > 0:
            the_noun = pargs[0]
        else:
            the_noun = self.instanceName
        the_noun = re.sub(r'.*\.', '', the_noun)
        return the_noun        
    def as_noun(self, *pargs):
        if not self.gathering:
            self.gathered
        if len(pargs) > 0:
            the_noun = pargs[0]
        else:
            the_noun = self.instanceName
        the_noun = re.sub(r'.*\.', '', the_noun)
        if len(self.elements) > 1 or len(self.elements) == 0:
            return noun_plural(the_noun)
        else:
            return the_noun
    def number(self):
        if not self.gathering:
            self.gathered
        return len(self.elements)
    def number_as_word(self):
        if not self.gathering:
            self.gathered
        return nice_number(self.number())
    def comma_and_list(self):
        if not self.gathering:
            self.gathered
        return comma_and_list(self.elements)        
    def __getitem__(self, index):
        return self.elements[index]
    def __str__(self):
        return self.comma_and_list()

class PartyList(DAList):
    pass

class ChildList(DAList):
    pass

class FinancialList(DAObject):
    def init(self):
        self.elements = set()
        return super(FinancialList, self).init()
    def new(self, item, **kwargs):
        self.initializeAttribute(name=item, objectType=Value)
        self.elements.add(item)
        for arg in kwargs:
            setattr(getattr(self, item), arg, kwargs[arg])
    def total(self):
        result = 0
        for item in self.elements:
            if getattr(self, item).exists:
                result += Decimal(getattr(self, item).value)
        return(result)
    def __str__(self):
        return self.total()
    
class PeriodicFinancialList(DAObject):
    def init(self):
        self.elements = set()
        return super(PeriodicFinancialList, self).init()
    def new(self, item, **kwargs):
        self.initializeAttribute(name=item, objectType=PeriodicValue)
        self.elements.add(item)
        for arg in kwargs:
            setattr(getattr(self, item), arg, kwargs[arg])
    def total(self):
        if not self.gathering:
            self.gathered
        result = 0
        for item in self.elements:
            if getattr(self, item).exists:
                result += Decimal(getattr(self, item).value) * int(getattr(self, item).period)
        return(result)
    def __str__(self):
        return self.total()

class Income(PeriodicFinancialList):
    pass

class Asset(FinancialList):
    pass

class Expense(PeriodicFinancialList):
    pass

class Value(DAObject):
    pass

class PeriodicValue(Value):
    pass

class DAFile(DAObject):
    def init(self, **kwargs):
        if 'filename' in kwargs:
            self.filename = kwargs['filename']
        if 'mimetype' in kwargs:
            self.filename = kwargs['mimetype']
        if 'extension' in kwargs:
            self.filename = kwargs['extension']
        if 'number' in kwargs:
            self.number = kwargs['number']
            self.ok = True
        else:
            self.ok = False
        return
    def show(self, width=None):
        if not self.ok:
            return('')
        if width is not None:
            return('[IMAGE ' + str(self.number) + ', ' + str(width) + ']')
        else:
            return('[IMAGE ' + str(self.number) + ']')

class DAFileCollection(DAObject):
    pass

def send_email(to=None, sender=None, cc=None, bcc=None, body=None, html=None, subject="", attachments=[]):
    from flask_mail import Message
    #sys.stderr.write("moo1\n")
    if type(to) is not list or len(to) == 0:
        return False
    if body is None and html is None:
        body = ""
    #sys.stderr.write("moo2\n")
    email_stringer = lambda x: email_string(x, include_name=False)
    msg = Message(subject, sender=email_stringer(sender), recipients=email_stringer(to), cc=email_stringer(cc), bcc=email_stringer(bcc), body=body, html=html)
    success = True
    for attachment in attachments:
        #sys.stderr.write("moo31\n")
        if type(attachment) is DAFileCollection:
            subattachment = getattr(attachment, 'pdf', getattr(attachment, 'rtf', getattr(attachment, 'html', getattr(attachment, 'tex', None))))
            if subattachment is not None:
                attachment = subattachment
            else:
                success = False
        if type(attachment) is DAFile and attachment.ok:
            #sys.stderr.write("moo32\n")
            file_info = file_finder(str(attachment.number))
            if ('path' in file_info):
                #sys.stderr.write("moo33\n")
                failed = True
                with open(file_info['path'], 'r') as fp:
                    #sys.stderr.write("moo3\n")
                    msg.attach(file_info['filename'], file_info['mimetype'], fp.read())
                    failed = False
                if failed:
                    #sys.stderr.write("moo4\n")
                    success = False
            else:
                success = False
                #sys.stderr.write("moo34\n")
        else:
            success = False
            #sys.stderr.write("moo35\n")
    appmail = mail_variable()
    if not appmail:
        #sys.stderr.write("moo36\n")
        success = False
    if success:
        #sys.stderr.write("moo37\n")
        try:
            appmail.send(msg)
        except Exception as errmess:
            #sys.stderr.write("moo38: " + str(errmess) + "\n")
            success = False
    return(success)
    
def email_string(persons, include_name=None):
    if persons is None:
        return None
    if type(persons) is not list:
        persons = [persons]
    result = []
    for person in persons:
        if isinstance(person, Person):
            sys.stderr.write("email string: contemplating " + person.object_name() + "\n")
            result.append(person.email_address(include_name=include_name))
            sys.stderr.write("email string was" + person.email_address(include_name=include_name) + "\n")
        else:
            sys.stderr.write("email string not a person: contemplating " + str(person) + "\n")
            result.append(str(person))
    return result
