#!/usr/bin/python
import os
import sqlite3 as db
import re

CREATEMATRIALS = 'create table matrials(matrial integer primary key,categoryid integer, name varchar(64),price float, provider varchar(128))'
CREATECATEGORYES = 'create table categories(categoryid integer primary key autoincrement,category varchar(256) unique, categoryinfo varchar(64))'
CREATEBOMS = 'create table boms(id integer primary key autoincrement,matrial integer unique, name varchar(64),proname varchar(128),client varchar(128),contact varchar(256))'
CRBOM = 'create table %s(id integer primary key autoincrement, matrial interger unique, quantity interger, info varchar(64))'

INSERTMA = 'insert into matrials values(%d, %d, \"%s\", %f, \"%s\")'
INSERTCATEGORY = 'insert into categories (category, categoryinfo) values(\"%s\",\" %s\")'
INSERTBOM = 'insert into boms (matrial, name, proname, client, contact)values(%d, \"%s\", \"%s\", \"%s\", \"%s\")'
INSERTBOMMA = 'insert into %s (matrial, quantity, info) values(%d, %d, \"%s\")'

DROPBOM = 'drop table %s'
DELETEABOM = 'delete from boms where matrial=%d'
DELETEMA = 'delete from matrials where matrial=%d'
DELETEFORMBOM = 'delete from %s where matrial=%d'
UPDATEBOMBYMA = 'update %s set matrial=%d where matrial=%d'

CREATEBOMVIEW = 'create view bomview as select matrial,quantity,price,info from matrials inner join %s on %s.matrial = matrials.matrial'
SELECTBOMVIEW = 'select matrials.matrial,quantity,price,(price*quantity),info from matrials inner join %s on %s.matrial = matrials.matrial'
CACULATEPRICE = 'select sum(price*quantity) from matrials inner join %s on %s.matrial =  matrials.matrial'

SUBCATEGORY = 'select * from categories where category regexp \"^%s/[^/]+$\"'
GETALLCATEGORY = 'select category from categories where category regexp \"%s($|/.*)\"'
MATRIALVIEW = 'create view matrialview as select matrial,name,price,provider,category \
from categories inner join matrials on categories.categoryid = matrials.categoryid'
GETMALIST = 'select matrial,name,price,provider from matrialview where category regexp \"%s($|/.*)\"'
SELECTMABYCATEGORY = 'select matrial,name,price,provider,lastcomp(category) from matrialview where category=\"%s\"'
SELECTMAALL = 'select matrial,name,price,provider,lastcomp(category) from matrialview where category=\"%s\"'
#SELECTMABYCATEGORY = 'select matrial,name,price,provider from categories inner join matrials on categories.categoryid = matrials.categoryid where category=\"%s\"'
GETIDBYCATEGORYNAME = 'select categoryid from categories where category=\"%s\"'
UPDATECATEGORYS = 'update categories set category=\"%s\" where category=\"%s\"'
GETIDSBYCATE = 'select categoryid from categories where category regexp \"%s($|/.*)\"'
GETMABYCATE_R = 'select matrial from categories inner join matrials on categories.categoryid = matrials.categoryid where category regexp \"%s($|/.*)\"'
DELETECATEGPRYS = 'delete from categories where category regexp \"%s($|/.*)\"'

SEMI_GOODS = 4000000
SYSTEM_GOODS = 7000000
def iscompoundma(matrial):
    if (matrial >= SEMI_GOODS):
        return True
    else:
        return False

def issystemma(matrial):
    if (matrial >= SYSTEM_GOODS):
        return True
    else:
        return False

def regexp(pattern,subject):
    reg = re.compile(pattern)
    return reg.search(subject) is not None

m_last_component = re.compile('[^/]+$')
def get_last_category_component(subject):
    ret = m_last_component.search(subject)
    if ret is None:
        return ""
    else:
        return ret.group(0)

class erpdb(object):
    'data base for matrials and boms'
    myVersion = '1.0'
    def __init__ (self, dbdir='./db',dbname='erps.db'):
        if not os.path.isdir(dbdir):
            os.mkdir(dbdir)
        self.dbPath = os.path.join(dbdir, dbname)
        self.cxn = db.connect(self.dbPath)
        self.cxn.create_function('REGEXP', 2, regexp)
        self.cxn.create_function('LASTCOMP', 1, get_last_category_component)
        self.malist = [];

#    def __del__ (self):
#        self.cxn.close()
    def closedb(self):
        self.cxn.close()

    def createtables(self):
        cur = self.cxn.cursor()
        cur.execute(CREATEMATRIALS)
        cur.execute(CREATECATEGORYES)
        cur.execute(CREATEBOMS)
        cur.execute(MATRIALVIEW)
        #cur.execute(CRBOM % 'bom0001')
        cur.close()
        self.cxn.commit()

    def insert_ma(self, matrial, categoryid, name = "new", price = 0, provider = ""):
        ''' insert a new material to db '''
        cur = self.cxn.cursor()
        cur.execute(INSERTMA % (matrial, categoryid, name, price, provider))
        cur.close()
        self.cxn.commit()

    def insert_category(self, categoryname, fcategoryname = "", info = ""):
        ''' insert a new category under fcategoryname '''
        cur = self.cxn.cursor()
        cur.execute(INSERTCATEGORY % (fcategoryname + '/' + categoryname, info))
        cur.close()
        self.cxn.commit()

    def insert_fullcategory(self, fullcategoryname, info = ""):
        ''' insert a new category under fcategoryname '''
        cur = self.cxn.cursor()
        cur.execute(INSERTCATEGORY % (fullcategoryname, info))
        cur.close()
        self.cxn.commit()

    def insert_bom(self, matrial, name = "", proname = "", client = "", contact = ""):
        ''' insert a bom '''
        cur = self.cxn.cursor()
        cur.execute(INSERTBOM % (matrial, name, proname, client, contact))
        cur.close()
        self.cxn.commit()

    def createbom(self, bomname):
        ''' create a bom by bomname '''
        cur = self.cxn.cursor()
        cur.execute(CRBOM % bomname)
        cur.close()
        self.cxn.commit()

    def insert_bom_ma(self, bomname, matrial, quantity, info=""):
        ''' insert a matrial to bom '''
        cur = self.cxn.cursor()
        cur.execute(INSERTBOMMA % (bomname, matrial, quantity, info))
        cur.close()
        self.cxn.commit()

    def bomname_by_ma(self,matrial):
        return 'bom%d' % matrial

    def del_bom(self, matrial):
        ''' delete a bom from db '''
        bom_name = self.bomname_by_ma(matrial);
        cur = self.cxn.cursor()
        if matrial >= SEMI_GOODS:
            try:
                cur.execute(DELETEABOM % matrial)
                cur.execute(DROPBOM % bom_name)
            except db.DatabaseError, e:
                print 'del matrial bom error %s\n' % e
        cur.close()
        self.cxn.commit()

    def del_matrial_from_db(self, matrial):
        ''' delete a matrial from the db '''
        bom_name = self.bomname_by_ma(matrial);
        cur = self.cxn.cursor()
        cur.execute(DELETEMA % matrial)
        if matrial >= SEMI_GOODS:
            try:
                cur.execute(DELETEABOM % matrial)
                cur.execute(DROPBOM % bom_name)
            except db.DatabaseError, e:
                print 'del matrial bom error %s\n' % e
        cur.close()
        self.cxn.commit()

    def del_matrial_from_bom(self, bomname, matrial):
        ''' delete a matrial from bomname '''
        cur = slef.cxn.cursor()
        cur.execute(DELETEFORMBOM % (bomname, matrial))
        cur.close()
        self.cxn.commit()

    def update_bom_by_matrial(self, bomname, oldmatrial, newmatrial):
        ''' alter the item whose matrial is oldmatiral to new item whose matrial
        is newmatrial'''
        cur = slef.cxn.cursor()
        cur.execute(UPDATEBOMBYMA % (bomname, oldmatrial, newmatrial))
        cur.close()
        self.cxn.commit()

    def get_bom_by_matrial(self, matrial):
        ''' get a matrial's bom items '''
        bom_name = self.bomname_by_ma(matrial)
        cur = self.cxn.cursor()
        cur.execute(SELECTBOMVIEW % (bom_name, bom_name))
        for eachitem in cur.fetchall():
            print eachitem
        cur.close()

    def get_total_price_from_bom(self, matrial):
        ''' get total price of a matrial's bom '''
        bom_name = self.bomname_by_ma(matrial)
        cur = self.cxn.cursor()
        cur.execute(CACULATEPRICE % (bom_name, bom_name))
        ret = cur.fetchone()
        cur.close()
        print ret
        if ret is None:
            return 0
        else:
            return ret[0]

    def get_sub_category(self,fcategory):
        cur = self.cxn.cursor()
        cur.execute(SUBCATEGORY % fcategory)
        for eachitem in cur.fetchall():
            print eachitem
        cur.close()

    def get_ma_by_category(self, categoryname):
        cur = self.cxn.cursor()
        cur.execute(SELECTMABYCATEGORY % categoryname)
        for eachitem in cur.fetchall():
            print eachitem
        cur.close()

    def get_id_by_categoryname(self, categoryname):
        cur = self.cxn.cursor()
        cur.execute(GETIDBYCATEGORYNAME % categoryname)
        ret = cur.fetchone()
        print ret
        cur.close()
        if ret is not None:
            return ret[0]
        else:
            return 0

    def get_categories_name(self,root = ''):
        cur = self.cxn.cursor()
        cur.execute(GETALLCATEGORY % root)
        for eachitem in cur.fetchall():
            print eachitem
            yield eachitem[0]
        cur.close()

    def update_categories_by_name(self, newcate, oldcate):
        cur = self.cxn.cursor()
        cur.execute(UPDATECATEGORYS % (newcate, oldcate))
        cur.close()
        self.cxn.commit()

    def get_ma_by_cate(self, cate):
        cur = self.cxn.cursor()
        cur.execute(GETMABYCATE_R % cate)
        mas = []
        for eachitem in cur.fetchall():
            print eachitem
            mas.append(eachitem[0])
        cur.close()
        return mas

    def delete_categories(self, cate):
        mas = self.get_ma_by_cate(cate)
        for ma in mas:
            self.del_matrial_from_db(ma)
        cur = self.cxn.cursor()
        cur.execute(DELETECATEGPRYS % cate)
        cur.close()
        self.cxn.commit()

    def set_data_source(self, cate):
        cur = self.cxn.cursor()
        cur.execute(GETMALIST % cate)
        del self.malist
        self.malist = cur.fetchall();
        if self.malist is None or len(self.malist) < 1:
            self.malist = [[0,'',0,'']]
        cur.close()
        return self.malist

        

if __name__ == '__main__':
    testdb = erpdb()
    testdb.createtables()
    testdb.insert_category('standard','','standard items')
    testdb.insert_category('analyzer','','analyzers for gas')
    testdb.insert_category('screw','/standard','')
    testdb.insert_category('system','','')
    clid = testdb.get_id_by_categoryname('/standard/screw')
    testdb.insert_ma(1000001,clid, 'screw 5*5',0.8, 'provider 1')
    testdb.insert_ma(1000002,clid, 'screw 5*8',0.8, 'provider 1')

    clid = testdb.get_id_by_categoryname('/standard')
    testdb.insert_ma(1000003,clid, 'flat pad d5',0.8, 'provider 1')

    clid = testdb.get_id_by_categoryname('/analyzer')
    testdb.insert_ma(1000004,clid,'analyzer co',50000, 'provider 2')
    testdb.insert_ma(1000005,clid,'analyzer so2',40000, 'provider 2')

    clid = testdb.get_id_by_categoryname('/system')
    testdb.insert_ma(7000001,clid,'factory 1',0, '')

    testdb.insert_bom(7000001,'7000001','co for factory1','client 1', '10088')
    testdb.createbom(testdb.bomname_by_ma(7000001))
    testdb.insert_bom_ma(testdb.bomname_by_ma(7000001), 1000001, 2,'')
    testdb.insert_bom_ma(testdb.bomname_by_ma(7000001), 1000002, 1,'')
    testdb.get_bom_by_matrial(7000001)
    testdb.get_total_price_from_bom(7000001)

    testdb.get_ma_by_category('/standard/screw')
    testdb.closedb()

