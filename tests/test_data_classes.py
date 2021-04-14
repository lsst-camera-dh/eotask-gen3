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


def runSchemaTests(forWhom, testClass, tmpDir, ctorKwds):
    testObj = testClass(**ctorKwds)
    for oldSchemaClass in testClass.PREVIOUS_SCHEMAS:
        oldTestObj = testClass(schema=oldSchemaClass(), **ctorKwds)
        fname = os.path.join(tmpDir, '%s.fits' % oldSchemaClass.__name__)
        oldTestObj.writeFits(fname)
        matchObj = testClass.readFits(fname)
        assert oldTestObj.reportDiffValues(matchObj, sys.stderr)
        assert not (testObj == matchObj)
        
        
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
        """ Add tests as member functions """
        if 'testCtor' in testClass.testData:
            testCtorData = testClass.testData['testCtor']
            ctorTestFunc = partial(runCtorTests, cls, testClass, testCtorData)
            setattr(cls, 'testCtor%s' % className, ctorTestFunc)
            ioLoopbackTestFunc = partial(runIOLoopbackTests, cls, testClass, cls.tmpDir, testCtorData)
            setattr(cls, 'testIOLoopback%s' % className, ioLoopbackTestFunc)
            convertLoopbackTestFunc = partial(runConvertLoopbackTests, cls, testClass, testCtorData)
            setattr(cls, 'testCoverntLoopback%s' % className, convertLoopbackTestFunc)
            if testClass.PREVIOUS_SCHEMAS:
                schemaTestFunc = partial(runSchemaTests, cls, testClass, cls.tmpDir, testCtorData)
                setattr(cls, 'testSchema%s' % className, schemaTestFunc)        
            
    @classmethod
    def autoAdd(cls, classList):
        """ Add tests as member functions """
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
