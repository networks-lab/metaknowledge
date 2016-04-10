#Written by Reid McIlroy-Young for Dr. John McLevey, University of Waterloo 2015
import unittest
import metaknowledge
import metaknowledge.WOS
import os
import filecmp
import networkx as nx

disableJournChecking = True

class TestRecordCollection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        metaknowledge.VERBOSE_MODE = False
        cls.RCmain = metaknowledge.RecordCollection("metaknowledge/tests/testFile.isi")
        cls.RCbadmain = metaknowledge.RecordCollection("metaknowledge/tests/badFile.isi")

    def setUp(self):
        self.RC = self.RCmain.copy()
        self.RCbad = self.RCbadmain.copy()

    def test_isCollection(self):
        self.assertIsInstance(self.RC, metaknowledge.RecordCollection)
        self.assertEqual(str(metaknowledge.RecordCollection()), "RecordCollection(Empty)")
        self.assertTrue(self.RC == self.RC)

    def test_fullRead(self):
        RC = metaknowledge.RecordCollection("metaknowledge/tests/")
        self.assertEqual(len(RC), 812)

    def test_caching(self):
        RC = metaknowledge.RecordCollection("metaknowledge/tests/", cached = True, name = 'testingCache', extension = 'testFile.isi')
        self.assertTrue(os.path.isfile("metaknowledge/tests/tests.[testFile.isi].mkRecordDirCache"))
        accessTime = os.stat("metaknowledge/tests/testFile.isi").st_atime
        RC2 = metaknowledge.RecordCollection("metaknowledge/tests/", cached = True, name = 'testingCache', extension = 'testFile.isi')
        self.assertEqual(accessTime, os.stat("metaknowledge/tests/testFile.isi").st_atime)
        RC.dropBadEntries()
        RC2.dropBadEntries()
        self.assertEqual(RC, RC2)
        os.remove("metaknowledge/tests/tests.[testFile.isi].mkRecordDirCache")

    def test_bad(self):
        self.assertTrue(metaknowledge.RecordCollection('metaknowledge/tests/badFile.isi').bad)
        with self.assertRaises(metaknowledge.mkExceptions.RCTypeError):
            metaknowledge.RecordCollection('metaknowledge/tests/testFile.isi', extension = '.txt')
        self.assertEqual(self.RCbad | self.RC, self.RCbad | self.RC )
        self.assertEqual(len(self.RCbad | self.RCbad), 32)
        self.assertFalse(self.RCbad == self.RC)
        self.assertEqual('metaknowledge/tests/badFile.isi', self.RCbad.errors.keys().__iter__().__next__())

    def test_badEntries(self):
        badRecs = self.RC.badEntries()
        self.assertTrue(badRecs <= self.RC)
        self.assertTrue(badRecs.pop().bad)
        self.RC.dropBadEntries()

    def test_dropJourn(self):
        RCcopy = self.RC.copy()
        self.RC.dropNonJournals()
        self.assertEqual(len(self.RC), len(RCcopy) - 2)
        self.RC.dropNonJournals(invert = True)
        self.assertEqual(len(self.RC), 0)
        RCcopy.dropNonJournals(ptVal = 'B')
        self.assertEqual(len(RCcopy), 1)

    def test_repr(self):
        self.assertEqual(repr(self.RC), "<metaknowledge.RecordCollection object testFile>")

    def test_hash(self):
        self.assertNotEqual(hash(self.RC), hash(self.RCbad))
        R = self.RC.pop()
        RC = metaknowledge.RecordCollection([R])
        self.assertEqual(hash(RC), hash(hash(R)))

    def test_contains(self):
        R = self.RC.peak()
        self.assertTrue(R in self.RC)
        R = self.RC.pop()
        self.assertFalse(R in self.RC)

    def test_conID(self):
        R = self.RC.peak()
        self.assertTrue(self.RC.containsID(R.id))
        self.assertFalse(self.RC.containsID('234567654'))

    def test_discard(self):
        R = self.RC.peak()
        l = len(self.RC)
        self.RC.discard(R)
        l2 = len(self.RC)
        self.assertEqual(l, l2 + 1)
        self.RC.discard(R)
        self.assertEqual(l2, len(self.RC))

    def test_pop(self):
        R = self.RC.pop()
        self.assertFalse(R in self.RC)
        self.RC.clear()
        with self.assertRaises(KeyError):
            R = self.RC.pop()

    def test_peak(self):
        R = self.RC.peak()
        self.assertTrue(R in self.RC)
        self.RC.clear()
        R = self.RC.peak()
        self.assertTrue(R is None)

    def test_clear(self):
        R = self.RCbad.peak()
        self.assertTrue(self.RCbad.bad)
        self.RCbad.clear()
        self.assertFalse(self.RCbad.bad)
        self.assertFalse(R in self.RCbad)

    def test_remove(self):
        R = self.RC.peak()
        l = len(self.RC)
        self.RC.remove(R)
        self.assertEqual(l, len(self.RC) + 1)
        with self.assertRaises(KeyError):
            self.RC.remove(R)

    def test_equOps(self):
        l = len(self.RC)
        for i in range(10):
            self.RCbad.pop()
        lb = len(self.RCbad)
        RC = metaknowledge.RecordCollection([])
        RC.bad = True
        RC |= self.RC
        self.assertEqual(self.RC, RC)
        RC -= self.RC
        self.assertNotEqual(self.RC, RC)
        RC ^= self.RC
        self.assertEqual(self.RC, RC)
        RC &= self.RCbad
        self.assertNotEqual(self.RC, RC)

    def test_newOps(self):
        l = len(self.RC)
        for i in range(10):
            self.RCbad.pop()
        lb = len(self.RCbad)
        RC = metaknowledge.RecordCollection([])
        RC.bad = True
        RC3 = self.RC | RC
        self.assertEqual(self.RC, RC3)
        RC4 = RC3 - self.RC
        self.assertNotEqual(self.RC, RC4)
        RC5 = RC4 ^ self.RC
        self.assertEqual(self.RC, RC5)
        RC6 = RC5 & self.RCbad
        self.assertNotEqual(self.RC, RC6)

    def test_opErrors(self):
        with self.assertRaises(TypeError):
            self.RC <= 1
        with self.assertRaises(TypeError):
            self.RC >= 1
        self.assertTrue(self.RC != 1)
        with self.assertRaises(TypeError):
            self.RC >= 1
        with self.assertRaises(TypeError):
            self.RC |= 1
        with self.assertRaises(TypeError):
            self.RC ^= 1
        with self.assertRaises(TypeError):
            self.RC &= 1
        with self.assertRaises(TypeError):
            self.RC -= 1
        with self.assertRaises(TypeError):
            self.RC | 1
        with self.assertRaises(TypeError):
            self.RC ^ 1
        with self.assertRaises(TypeError):
            self.RC & 1
        with self.assertRaises(TypeError):
            self.RC - 1

    def test_addRec(self):
        l = len(self.RC)
        R = self.RC.pop()
        self.assertEqual(len(self.RC), l - 1)
        self.RC.add(R)
        self.assertEqual(len(self.RC), l)
        RC2 = metaknowledge.RecordCollection("metaknowledge/tests/TwoPaper.isi")
        self.RC |= RC2
        self.assertEqual(len(self.RC), l + 2)
        with self.assertRaises(metaknowledge.CollectionTypeError):
            self.RC.add(1)

    def test_bytes(self):
        with self.assertRaises(metaknowledge.BadRecord):
            self.assertIsInstance(bytes(self.RC), bytes)
        self.RC.dropBadEntries()
        self.assertIsInstance(bytes(self.RC), bytes)

    def test_WOS(self):
        self.RC.dropBadEntries()
        R = self.RC.peak()
        l = len(self.RC)
        self.assertTrue(R, self.RC.getID(R.id))
        self.assertEqual(len(self.RC), l)
        self.RC.removeID(R.id)
        self.assertEqual(len(self.RC), l - 1)
        self.RC.getID(self.RC.peak().id)
        self.assertEqual(len(self.RC), l - 1)
        self.assertFalse(self.RC.getID(self.RC.pop().id))
        self.RC.discardID('sdfghjkjhgfdfghj')
        self.RC.discardID('WOS:A1979GV55600001')
        with self.assertRaises(KeyError):
            self.RC.removeID('ghjkljhgfdfghjmh')

    def test_directoryRead(self):
        self.assertEqual(len(metaknowledge.RecordCollection('.')), 0)
        self.assertTrue(metaknowledge.RecordCollection('metaknowledge/tests/') >= self.RC)
        self.assertTrue(metaknowledge.RecordCollection('metaknowledge/tests/', extension= '.txt') <= self.RC)

    def test_contentType(self):
        RC = metaknowledge.RecordCollection('metaknowledge/tests/')
        self.assertEqual(RC._collectedTypes, {'MedlineRecord', 'WOSRecord', 'ProQuestRecord'})
        self.assertEqual(self.RC._collectedTypes, {'WOSRecord'})

    def test_write(self):
        fileName = 'OnePaper2.isi'
        RC = metaknowledge.RecordCollection('metaknowledge/tests/' + fileName)
        RC.writeFile(fileName + '.tmp')
        RC.writeFile()
        self.assertTrue(filecmp.cmp('metaknowledge/tests/' + fileName, fileName + '.tmp'))
        self.assertTrue(filecmp.cmp('metaknowledge/tests/' + fileName, RC.name + '.txt'))
        os.remove(fileName + '.tmp')
        os.remove(RC.name + '.txt')

    def test_writeCSV(self):
        filename = "test_writeCSV_temporaryFile.csv"
        if os.path.isfile(filename):
            os.remove(filename)
        self.RC.writeCSV(filename, onlyTheseTags=['UT', 'PT', 'TI', 'AF','J9' ,'CR', 'pubMedID'], firstTags = ['CR', 'UT', 'J9', 'citations'], csvDelimiter = '∂', csvQuote='≠', listDelimiter= '«', longNames=True, numAuthors = False)
        self.assertTrue(os.path.isfile(filename))
        self.assertEqual(os.path.getsize(filename), 114018)
        os.remove(filename)
        self.RC.writeCSV(filename)
        self.assertTrue(os.path.isfile(filename))
        self.assertEqual(os.path.getsize(filename), 109193)
        os.remove(filename)

    def test_writeBib(self):
        filename = 'testFile.bib'
        if os.path.isfile(filename):
            os.remove(filename)
        self.RC.writeBib(maxStringLength = 100)
        self.assertEqual(os.path.getsize(filename), 106458)
        os.remove(filename)
        self.RC.writeBib(fname = filename, wosMode = True, reducedOutput = True, niceIDs = False)
        self.assertEqual(os.path.getsize(filename), 17038)
        os.remove(filename)

    def test_makeDict(self):
        d = self.RC.makeDict(onlyTheseTags = list(metaknowledge.WOS.tagsAndNameSet), longNames = True)
        self.assertEqual(len(d), 62)
        self.assertEqual(len(d['wosString']), len(self.RC))
        if d['eISSN'][0] == '2155-3165':
            self.assertEqual(d['eISSN'][1], None)
        else:
            self.assertEqual(d['eISSN'][0], None)
        self.assertIsInstance(d['citations'], list)
        d = self.RC.makeDict(longNames = False, raw = True, numAuthors = False)
        self.assertEqual(len(d), 42)
        self.assertEqual(len(d['UT']), len(self.RC))
        self.assertIsInstance(d['CR'], list)

    def test_coCite(self):
        Gdefault = self.RC.coCiteNetwork(fullInfo = True)
        Gauths = self.RC.coCiteNetwork(nodeType = "author", dropAnon = False, detailedCore = True)
        GauthsNoExtra = self.RC.coCiteNetwork(nodeType = "author", nodeInfo = False)
        Gunwei = self.RC.coCiteNetwork(nodeType = 'original', weighted = False)
        if not disableJournChecking:
            Gjour = self.RC.coCiteNetwork(nodeType = "journal", dropNonJournals = True)
        Gyear = self.RC.coCiteNetwork(nodeType = "year", fullInfo = True, count = False)
        Gcore = self.RC.coCiteNetwork(detailedCore = ['AF','AU', 'DE', 'ID', 'PY'], coreOnly = True)
        Gexplode = self.RC.coCiteNetwork(expandedCore = True, keyWords = 'a')
        self.assertIsInstance(Gdefault, nx.classes.graph.Graph)
        self.assertLessEqual(len(Gdefault.edges()), len(Gunwei.edges()))
        self.assertLessEqual(len(Gdefault.nodes()), len(Gunwei.nodes()))
        self.assertEqual(len(GauthsNoExtra.edges()), len(Gauths.edges()))
        self.assertEqual(len(GauthsNoExtra.nodes()), len(Gauths.nodes()) - 1 )
        self.assertTrue('weight' in Gdefault.edges(data = True)[0][2])
        self.assertTrue('info' in Gdefault.nodes(data = True)[0][1])
        self.assertTrue('fullCite' in Gdefault.nodes(data = True)[0][1])
        self.assertFalse('weight' in Gunwei.edges(data = True)[0][2])
        self.assertEqual(metaknowledge.graphStats(Gdefault), "The graph has 493 nodes, 13011 edges, 0 isolates, 22 self loops, a density of 0.107282 and a transitivity of 0.611431")
        self.assertEqual(metaknowledge.graphStats(Gauths), "The graph has 321 nodes, 6733 edges, 1 isolates, 68 self loops, a density of 0.131094 and a transitivity of 0.598575")
        self.assertEqual(metaknowledge.graphStats(Gyear), "The graph has 91 nodes, 1926 edges, 0 isolates, 55 self loops, a density of 0.47033 and a transitivity of 0.702332")
        if not disableJournChecking:
            self.assertEqual(len(Gjour.nodes()), 85)
            self.assertEqual(len(Gjour.edges()), 1195)
            self.assertTrue('info' in Gjour.nodes(data=True)[0][1])
        self.assertTrue('info' in Gyear.nodes(data=True)[0][1])
        self.assertTrue('fullCite' in Gyear.nodes(data = True)[0][1])
        self.assertEqual(Gcore.node['Costadebeauregard O, 1975, CAN J PHYS']['info'], 'COSTADEBEAUREGARD O, COSTADEBEAUREGARD O')
        self.assertEqual(metaknowledge.graphStats(Gexplode), "The graph has 73 nodes, 369 edges, 0 isolates, 5 self loops, a density of 0.140411 and a transitivity of 0.523179")

    def test_coAuth(self):
        Gdefault = self.RC.coAuthNetwork()
        if not disableJournChecking:
            Gdetailed = self.RC.coAuthNetwork(count = False, weighted = False, detailedInfo = True, dropNonJournals = True)
        self.assertIsInstance(Gdefault, nx.classes.graph.Graph)
        self.assertEqual(len(Gdefault.nodes()), 45)
        self.assertEqual(len(Gdefault.edges()), 46)
        if not disableJournChecking:
            self.assertEqual(metaknowledge.graphStats(Gdetailed), 'The graph has 45 nodes, 46 edges, 9 isolates, 0 self loops, a density of 0.0464646 and a transitivity of 0.822581')

    def test_cite(self):
        Gdefault = self.RC.citationNetwork(fullInfo = True, count = False, dropAnon = True)
        Ganon = self.RC.citationNetwork(dropAnon = False)
        Gauths = self.RC.citationNetwork(nodeType = "author", detailedCore = True, dropAnon = True)
        GauthsNoExtra = self.RC.citationNetwork(nodeType = "author", nodeInfo = False, dropAnon = True)
        Gunwei = self.RC.citationNetwork(nodeType = 'original', weighted = False)
        if not disableJournChecking:
            Gjour = self.RC.citationNetwork(nodeType = "author", dropNonJournals = True, nodeInfo = True, count = False)
        Gyear = self.RC.citationNetwork(nodeType = "year", nodeInfo = True)
        Gcore = self.RC.citationNetwork(detailedCore = True, coreOnly = False)
        Gexplode = self.RC.citationNetwork(expandedCore = True, keyWords = ['b', 'c'])
        self.assertIsInstance(Gdefault, nx.classes.digraph.DiGraph)
        self.assertLessEqual(len(Gdefault.edges()), len(Gunwei.edges()))
        self.assertLessEqual(len(Gdefault.nodes()), len(Gunwei.nodes()))
        self.assertEqual(len(GauthsNoExtra.edges()), len(Gauths.edges()))
        self.assertEqual(len(GauthsNoExtra.nodes()), len(Gauths.nodes()))
        self.assertTrue('weight' in Gdefault.edges(data = True)[0][2])
        self.assertTrue('info' in Gdefault.nodes(data = True)[0][1])
        self.assertFalse('weight' in Gunwei.edges(data = True)[0][2])
        self.assertEqual(metaknowledge.graphStats(Gdefault), "The graph has 510 nodes, 816 edges, 1 isolates, 0 self loops, a density of 0.00314342 and a transitivity of 0.00600437")
        self.assertEqual(metaknowledge.graphStats(Ganon), "The graph has 511 nodes, 817 edges, 0 isolates, 0 self loops, a density of 0.00313495 and a transitivity of 0.00600437")
        self.assertEqual(metaknowledge.graphStats(Gauths), "The graph has 324 nodes, 568 edges, 1 isolates, 15 self loops, a density of 0.00542751 and a transitivity of 0.0210315")
        if not disableJournChecking:
            self.assertEqual(len(Gjour.edges()), 432)
            self.assertTrue('info' in Gjour.nodes(data=True)[0][1])
        self.assertTrue('info' in Gyear.nodes(data=True)[0][1])
        self.assertEqual(Gcore.node['Gilles H, 2002, OPT LETT']['info'], 'Gilles H, Simple technique for measuring the Goos-Hanchen effect with polarization modulation and a position-sensitive detector, OPTICS LETTERS, 27, 1421')
        self.assertEqual(metaknowledge.graphStats(Gexplode), "The graph has 19 nodes, 29 edges, 0 isolates, 3 self loops, a density of 0.0847953 and a transitivity of 0.132075")

    def test_oneMode(self):
        Gcr  = self.RC.oneModeNetwork('CR')
        Gcite = self.RC.oneModeNetwork('citations', nodeCount = False, edgeWeight = False)
        GcoCit = self.RC.coCiteNetwork()
        Gtit = self.RC.oneModeNetwork('title')
        stemFunc = lambda x: x[:-1]
        Gstem = self.RC.oneModeNetwork('keywords', stemmer = stemFunc)
        self.assertEqual(len(Gcite.edges()), len(Gcr.edges()))
        self.assertEqual(len(Gcite.nodes()), len(Gcr.nodes()))
        self.assertAlmostEqual(len(Gcite.nodes()), len(GcoCit.nodes()), delta = 50)
        self.assertEqual(len(self.RC.oneModeNetwork('D2').nodes()), 0)
        self.assertEqual(len(Gtit.nodes()), 31)
        self.assertEqual(len(Gtit.edges()), 0)
        self.assertEqual(len(self.RC.oneModeNetwork('email').edges()), 3)
        self.assertEqual(len(self.RC.oneModeNetwork('UT').nodes()), len(self.RC) - 1)
        self.assertEqual(metaknowledge.graphStats(Gstem), 'The graph has 41 nodes, 142 edges, 2 isolates, 0 self loops, a density of 0.173171 and a transitivity of 0.854015')
        self.assertIsInstance(Gstem.nodes()[0], str)
        with self.assertRaises(TypeError):
            G = self.RC.oneModeNetwork(b'Not a Tag')
            del G

    def test_twoMode(self):
        self.RC.dropBadEntries()
        Gutti = self.RC.twoModeNetwork('UT', 'title', directed = True, recordType = False)
        Gafwc = self.RC.twoModeNetwork('AF', 'WC', nodeCount = False, edgeWeight = False)
        Gd2em = self.RC.twoModeNetwork('D2', 'email')
        Gemd2 = self.RC.twoModeNetwork('email', 'D2')
        Gstemm = self.RC.twoModeNetwork('title', 'title', stemmerTag1 = lambda x: x[:-1], stemmerTag2 = lambda x: x + 's')
        self.assertIsInstance(Gutti, nx.classes.digraph.DiGraph)
        self.assertIsInstance(Gafwc, nx.classes.graph.Graph)
        self.assertEqual(Gutti.edges('WOS:A1979GV55600001')[0][1][:31], "EXPERIMENTS IN PHENOMENOLOGICAL")
        self.assertEqual(len(Gutti.nodes()), 2 * len(self.RC) - 1)
        with self.assertRaises(TypeError):
            G = self.RC.twoModeNetwork('TI', b'not a tag')
            del G
        with self.assertRaises(TypeError):
            G = self.RC.twoModeNetwork(b'Not a Tag', 'TI')
            del G
        self.assertTrue(nx.is_isomorphic(Gd2em, Gemd2))
        self.assertEqual(metaknowledge.graphStats(Gstemm), 'The graph has 62 nodes, 31 edges, 0 isolates, 0 self loops, a density of 0.0163934 and a transitivity of 0')
        self.assertTrue('Optical properties of nanostructured thin filmss' in Gstemm)

    def test_nMode(self):
        G = self.RC.nModeNetwork(metaknowledge.WOS.tagToFullDict.keys())
        Gstem = self.RC.nModeNetwork(metaknowledge.WOS.tagToFullDict.keys(), stemmer = lambda x : x[0])
        self.assertEqual(metaknowledge.graphStats(G), 'The graph has 1186 nodes, 38592 edges, 0 isolates, 56 self loops, a density of 0.0549192 and a transitivity of 0.295384')
        self.assertEqual(metaknowledge.graphStats(Gstem), 'The graph has 50 nodes, 1015 edges, 0 isolates, 35 self loops, a density of 0.828571 and a transitivity of 0.855834')

    def test_localCiteStats(self):
        d = self.RC.localCiteStats()
        dPan = self.RC.localCiteStats(pandasFriendly = True)
        dYear = self.RC.localCiteStats(keyType = 'year')
        self.assertEqual(d[metaknowledge.Citation("Azzam R. M. A., 1977, ELLIPSOMETRY POLARIZ")], 1)
        self.assertEqual(len(dPan['Citations']),len(d))
        self.assertTrue(dPan['Citations'][0] in d)
        self.assertEqual(dYear[2009], 2)

    def test_localCitesOf(self):
        C = metaknowledge.Citation("COSTADEB.O, 1974, LETT NUOVO CIMENTO, V10, P852")
        self.assertEqual("WOS:A1976CW02200002", self.RC.localCitesOf(C).peak().id)
        self.assertEqual(self.RC.localCitesOf(self.RC.peak().id),
         self.RC.localCitesOf(self.RC.peak().createCitation()))

    def test_citeFilter(self):
        RCmin = self.RC.citeFilter('', reverse = True)
        RCmax = self.RC.citeFilter('')
        RCanon = self.RC.citeFilter('', 'anonymous')
        RC1970 = self.RC.citeFilter(1970, 'year')
        RCno1970 = self.RC.citeFilter(1970, 'year', reverse = True)
        RCMELLER = self.RC.citeFilter('meller', 'author')
        self.assertEqual(len(RCmin), 0)
        self.assertEqual(len(RCmax), len(self.RC))
        self.assertEqual(len(RCanon), 1)
        self.assertEqual(len(RC1970), 15)
        self.assertEqual(len(RC1970) + len(RCno1970), len(self.RC))
        self.assertEqual(len(RCMELLER), 1)
        RCnocite = metaknowledge.RecordCollection('metaknowledge/tests/OnePaperNoCites.isi')
        self.assertEqual(len(RCnocite.citeFilter('')), 0)
