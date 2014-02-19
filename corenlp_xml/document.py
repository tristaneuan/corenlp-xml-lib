"""
Sub-module for handling document-level stuff
"""
from lxml import etree
from collections import OrderedDict
from nltk import Tree
from dependencies import DependencyGraph
from coreference import Coreference


class Document:
    """
    This class abstracts a Stanford CoreNLP Document
    """

    def __init__(self, xml_string):
        """
        Constructor method.
        :param xml_string: The XML string we're going to parse and represent, coming from CoreNLP
        :type xml_string: str
        """
        self._sentences_dict = None
        self._sentiment = None
        self._xml_string = xml_string
        self._xml = etree.fromstring(xml_string)
        self._coreferences = None

    @property
    def sentiment(self):
        """
        Returns average sentiment of document.
        :return: average sentiment of the document
        :rtype: float
        """
        if self._sentiment is None:
            results = self._xml.xpath('/root/document/sentences')
            self._sentiment = float(results[0].get("averageSentiment", 0)) if len(results) > 0 else None
        return self._sentiment

    def _get_sentences_dict(self):
        """
        Returns sentence objects
        :return: order dict of sentences
        :rtype:class:`OrderedDict`
        """
        if self._sentences_dict is None:
            sentences = [Sentence(element) for element in self._xml.xpath('/root/document/sentences/sentence')]
            self._sentences_dict = OrderedDict([(s.id, s) for s in sentences])
        return self._sentences_dict

    @property
    def sentences(self):
        """
        Returns the ordered dict of sentences as a list.
        :return: list of sentences, in order
        :rtype:list
        """
        return self._get_sentences_dict().values()

    def get_sentence_by_id(self, id):
        """
        :param id: the ID of the sentence, as defined in the XML
        :type id: int
        :return:class:`Sentence`
        """
        return self._get_sentences_dict().get(id)

    @property
    def coreferences(self):
        """
        Returns a list of Coreference classes
        :return: list
        :rtype: list of `corenlp_xml.coreference.Coreference`
        """
        if self._coreferences is None:
            coreferences = self._xml.xpath('/root/document/coreference/coreference')
            if len(coreferences) > 0:
                self._coreferences = [Coreference(self, element) for element in coreferences]
        return self._coreferences


class Sentence():
    """
    This abstracts a sentence
    """

    def __init__(self, element):
        """
        Constructor method
        :param element: An etree element.
        :type element:class:`lxml.etree.ElementBase`
        """
        self._id = None
        self._sentiment = None
        self._tokens_dict = None
        self._element = None
        self._parse = None
        self._parse_string = None
        self._basic_dependencies = None
        self._collapsed_dependencies = None
        self._collapsed_ccprocessed_dependencies = None
        self._element = element

    @property
    def id(self):
        """
        :return: the ID attribute of the sentence
        :rtype id: int
        """
        if self._id is None:
            self._id = int(self._element.get('id'))
        return self._id

    @property
    def sentiment(self):
        """
        :return: the sentiment value of this sentence
        :rtype float:
        """
        if self._sentiment is None:
            self._sentiment = float(self._element.get('sentiment', 0))
        return self._sentiment

    def _get_tokens_dict(self):
        """
        :return: The ordered dict of the tokens
        :rtype:class:`OrderedDict`
        """
        if self._tokens_dict is None:
            tokens = [Token(element) for element in self._element.xpath('tokens/token')]
            self._tokens_dict = OrderedDict([(t.id, t) for t in tokens])
        return self._tokens_dict

    @property
    def tokens(self):
        """
        :return: a list of Token instances
        :rtype:list
        """
        return TokenList(self._get_tokens_dict().values())

    def get_token_by_id(self, id):
        """
        :param id: The XML ID of the token
        :type id: int
        :return: The token
        :rtype:class:`Token`
        """
        return self._get_tokens_dict().get(id)

    @property
    def parse_string(self):
        """
        :return: The parse string
        :rtype:str
        """
        if self._parse_string is None:
            parse_text = self._element.xpath('parse/text()')
            if len(parse_text) > 0:
                self._parse_string = parse_text[0]
        return self._parse_string

    @property
    def parse(self):
        """
        :return: The NLTK parse tree
        :rtype:class:`nltk.Tree`
        """
        if self.parse_string is not None and self._parse is None:
            self._parse = Tree.parse(self._parse_string)
        return self._parse

    @property
    def basic_dependencies(self):
        """
        :return: The dependency graph for basic dependencies
        :rtype:class:`DependencyGraph`
        """
        if self._basic_dependencies is None:
            deps = self._element.xpath('dependencies[@type="basic-dependencies"]')
            if len(deps) > 0:
                self._basic_dependencies = DependencyGraph(deps[0])
        return self._basic_dependencies

    @property
    def collapsed_dependencies(self):
        """
        :return: The dependency graph for collapsed dependencies
        :rtype:class:`DependencyGraph`
        """
        if self._basic_dependencies is None:
            deps = self._element.xpath('dependencies[@type="collapsed-dependencies"]')
            if len(deps) > 0:
                self._basic_dependencies = DependencyGraph(deps[0])
        return self._basic_dependencies

    @property
    def collapsed_ccprocessed_dependencies(self):
        """
        :return: The dependency graph for collapsed and cc processed dependencies
        :rtype:class:`DependencyGraph`
        """
        if self._basic_dependencies is None:
            deps = self._element.xpath('dependencies[@type="collapsed-ccprocessed-dependencies"]')
            if len(deps) > 0:
                self._basic_dependencies = DependencyGraph(deps[0])
        return self._basic_dependencies


class TokenList(list):

    def __init__(self, *args):
        super(TokenList, self).__init__(args[0])

    def __add__(self, rhs):
        return TokenList(list.__add__(self, rhs))

    def __getslice__(self, i ,j):
        return TokenList(list.__getslice__(self, i, j))

    def __add__(self, other):
        return TokenList(list.__add__(self, other))

    def __mul__(self, other):
        return TokenList(list.__mul__(self, other))

    def __str__(self):
        return " ".join([token.word for token in self])

    def __getitem__(self, item):
        result = list.__getitem__(self, item)
        try:
            return TokenList(result)
        except TypeError:
            return result


class Token():
    """
    Wraps the token XML element
    """

    def __init__(self, element):
        """
        Constructor method
        :param element: An etree element
        :type element:class:`lxml.etree.ElementBase`
        """
        self._id = None
        self._word = None
        self._lemma = None
        self._character_offset_begin = None
        self._character_offset_end = None
        self._pos = None
        self._ner = None
        self._speaker = None
        self._element = element

    @property
    def id(self):
        """
        Lazy-loads ID
        :return: The ID of the token element
        :rtype: int
        """
        if self._id is None:
            self._id = int(self._element.get('id'))
        return self._id

    @property
    def word(self):
        """
        Lazy-loads word value
        :return: The plain string value of the word
        :rtype: str
        """
        if self._word is None:
            words = self._element.xpath('word/text()')
            if len(words) > 0:
                self._word = words[0]
        return self._word

    @property
    def lemma(self):
        """
        Lazy-loads the lemma for this word
        :return: The plain string value of the word lemma
        :rtype: str
        """
        if self._lemma is None:
            lemmata = self._element.xpath('lemma/text()')
            if len(lemmata) > 0:
                self._lemma = lemmata[0]
        return self._lemma

    @property
    def character_offset_begin(self):
        """
        Lazy-loads character offset begin node
        :return: the integer value of the offset
        :rtype: int
        """
        if self._character_offset_begin is None:
            offsets = self._element.xpath('CharacterOffsetBegin/text()')
            if len(offsets) > 0:
                self._character_offset_begin = int(offsets[0])
        return self._character_offset_begin

    @property
    def character_offset_end(self):
        """
        Lazy-loads character offset end node
        :return: the integer value of the offset
        :rtype: int
        """
        if self._character_offset_end is None:
            offsets = self._element.xpath('CharacterOffsetEnd/text()')
            if len(offsets) > 0:
                self._character_offset_end = int(offsets[0])
        return self._character_offset_end

    @property
    def pos(self):
        """
        Lazy-loads the part of speech tag for this word
        :return: The plain string value of the POS tag for the word
        :rtype: str
        """
        if self._pos is None:
            poses = self._element.xpath('POS/text()')
            if len(poses) > 0:
                self._pos = poses[0]
        return self._pos

    @property
    def ner(self):
        """
        Lazy-loads the NER for this word
        :return: The plain string value of the NER tag for the word
        :rtype: str
        """
        if self._ner is None:
            ners = self._element.xpath('NER/text()')
            if len(ners) > 0:
                self._ner = ners[0]
        return self._ner

    @property
    def speaker(self):
        """
        Lazy-loads the speaker for this word
        :return: The plain string value of the speaker tag for the word
        :rtype: str
        """
        if self._speaker is None:
            speakers = self._element.xpath('Speaker/text()')
            if len(speakers) > 0:
                self._speaker = speakers[0]
        return self._speaker
