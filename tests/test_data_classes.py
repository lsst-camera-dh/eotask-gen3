import shutil
import os
import sys

from functools import partial
import unittest

from lsst.eotask_gen3 import GetEoCalibClassDict, WriteSchemaMarkdown

TEST_CLASSES = GetEoCalibClassDict()

def runCtorTests(forWhom, testClass, ctorKwds):
    testObj = testClass(**ctorKwds)

def runIOLoopbackTests(forWhom, testClass, tmpDir, ctorKwds):

    fname = os.path.join(tmpDir, '%s.fits' % testClass.__name__)
    testObj = testClass(**ctorKwds)
    testObj.writeFits(fname)
    matchObj = testClass.readFits(fname)
    assert testObj.reportDiffValues(matchObj, sys.stderr)
    assert testObj == matchObj

def runConvertLoopbackTests(forWhom, testClass, ctorKwds):

    testObj = testClass(**ctorKwds)
    testObjAsDict = testObj.toDict()

    testObjFromDict = testClass.fromDict(testObjAsDict)
    assert testObj.reportDiffValues(testObjFromDict, sys.stderr)



class DataClassesTestCase(unittest.TestCase):

    tmpDir = os.path.join('temp', 'test_data_classes')

    def setUp(self):
        try:
            os.makedirs(self.tmpDir)
        except FileExistsError:
            pass

    def tearDown(self):
        shutil.rmtree(self.tmpDir)

    @classmethod
    def autoAddClass(cls, className, testClass):
        """Add tests as member functions to a class"""
        if 'testCtor' in testClass.testData:
            ctorTestFunc = partial(runCtorTests, cls, testClass, testClass.testData['testCtor'])
            setattr(cls, 'testCtor%s' % className, ctorTestFunc)
            ioLoopbackTestFunc = partial(runIOLoopbackTests, cls, testClass, cls.tmpDir,
                                         testClass.testData['testCtor'])
            setattr(cls, 'testIOLoopback%s' % className, ioLoopbackTestFunc)
            convertLoopbackTestFunc = partial(runConvertLoopbackTests, cls, testClass,
                                              testClass.testData['testCtor'])
            setattr(cls, 'testCoverntLoopback%s' % className, convertLoopbackTestFunc)

    @classmethod
    def autoAdd(cls, classList):
        """Add tests as member functions to a class"""
        for className, testClass in classList.items():
            if hasattr(testClass, 'testData'):
                cls.autoAddClass(className, testClass)

    def testMarkdown(self):
        fname = os.path.join(self.tmpDir, 'schema.md')
        WriteSchemaMarkdown(fname)

    def testEqualityOp(self):

        readNoiseDataClass = TEST_CLASSES['EoReadNoiseData']
        ptcDataClass = TEST_CLASSES['EoPtcData']

        readNoiseData = readNoiseDataClass(**readNoiseDataClass.testData['testCtor'])
        ptcDataClass = ptcDataClass(**ptcDataClass.testData['testCtor'])

        assert readNoiseData != ptcDataClass
        
        
DataClassesTestCase.autoAdd(TEST_CLASSES)
