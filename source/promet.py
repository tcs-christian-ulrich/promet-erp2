import sys,os;sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import logging,warnings,sys,pathlib,os,sqlalchemy.ext.declarative,hashlib,sqlalchemy.event
from typing import Text
from sqlalchemy import Column, ForeignKey, Integer, BigInteger, String, func, update
from sqlalchemy import create_engine
from sqlalchemy.orm import relation, relationship, sessionmaker
from sqlalchemy.sql.sqltypes import DateTime, Float
import json,threading,urllib.parse,uuid
Table = sqlalchemy.ext.declarative.declarative_base()
session = None
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    class IDGenerator(Table):
        __tablename__ = 'GEN_SQL_ID'
        #id = Column('SQL_ID',BigInteger, primary_key=True, autoincrement=True)
        gid = Column('ID',BigInteger, primary_key=True)
    class BasicTable:
        RELATIONSHIPS_TO_DICT = False
        def __iter__(self):
            return self.to_dict().iteritems()
        def to_dict(self, rel=None, backref=None):
            if rel is None:
                rel = self.RELATIONSHIPS_TO_DICT
            res = self.__dict__
            del res['_sa_instance_state']
            #res = {column.key: getattr(self, attr)
            #       for attr, column in self.__mapper__.c.items()}
            if rel:
                for attr, relation in self.__mapper__.relationships.items():
                    # Avoid recursive loop between to tables.
                    try:
                        if backref == relation.table:
                            continue
                    except:
                        pass
                    value = getattr(self, attr)
                    if value is None:
                        res[relation.key] = None
                    elif isinstance(value.__class__, sqlalchemy.ext.declarative.DeclarativeMeta):
                        res[relation.key] = value.to_dict(backref=self.__table__)
                    else:
                        res[relation.key] = [i.to_dict(backref=self.__table__)
                                            for i in value]
            return res
        def to_json(self, rel=None):
            def extended_encoder(x):
                if isinstance(x, datetime):
                    return x.isoformat()
                if isinstance(x, uuid.UUID):
                    return str(x)
                else:
                    return str(x)
            if rel is None:
                rel = self.RELATIONSHIPS_TO_DICT
            return json.dumps(self.to_dict(rel), default=extended_encoder, indent=4)
        id = Column('SQL_ID',BigInteger, primary_key=True)
    class TimestampTable(BasicTable):
        TimestampD = Column("TIMESTAMPD",DateTime,default=datetime.utcnow, onupdate=datetime.utcnow)
    class User(Table,TimestampTable):
        __tablename__ = 'USERS'
        Type = Column('TYPE',String(1))
        Parent = Column('PARENT',BigInteger)
        AccountNo = Column('ACCOUNTNO',String(20),nullable=False);
        Name = Column('NAME',String(250), nullable=False)
        Password = Column('PASSWORD',String(45))
        Salt = Column('SALT',String(105))
        IdCode = Column('IDCODE',String(4));
        Employment = Column('EMPLOYMENT',DateTime)
        Leaved = Column('LEAVED',DateTime)
        CustomerNo = Column('CUSTOMERNO',String(20))
        PersonnelNo = Column('PERSONNELNO',String(20))
        Department = Column('DEPARTMENT',String(30))
        Position = Column('POSITION',String(30))
        LoginName = Column('LOGINNAME',String(30))
        eMail = Column('EMAIL',String(100))
        PayGroup = Column('PAYGROUP',BigInteger)
        WorkTime = Column('WORKTIME',Integer) #8 wenn NULL
        WeekWorkTime = Column('WEEKWORKTIME',Integer) #40 wenn NULL
        UseWorkTime = Column('USEWORKTIME',Integer)
        LoginActive = Column('LOGINACTIVE',String(1))
        RemoteAccess = Column('REMOTEACCESS',String(1))
        LastLogin = Column('LASTLOGIN',DateTime)
        AutoSource = Column('AUTHSOURCE',String(10))
        def mergeSalt(self,aPasswort, aSalt):
            Result = '';
            for i in range(len(aPasswort)):
                Result += aSalt[:5]
                aSalt = aSalt[5:]
                Result += aPasswort[:1]
                aPasswort = aPasswort[1:]
            return Result
        def checkPassword(self,password):
            if self.Password[:1] != '$':
                Result = hashlib.md5(password.encode()).hexdigest() == self.Password
            else:
                aRes = '$'+hashlib.sha1(hashlib.sha1(self.mergeSalt(password,self.Salt).encode()).hexdigest().encode()).hexdigest()
                Result = (aRes[:len(self.Password)] == self.Password) and (len(self.Password) > 30)
            Result = True
            return Result
    class BasicCreateableTable(TimestampTable):
        CreatedBy = Column("CREATEDBY",String(4))
    class BasicChangeableTable(BasicCreateableTable):
        ChangedBy = Column("CHANGEDBY",String(4))
    class OrderAddress(Table,TimestampTable):
        __tablename__ = 'ORDERADDR'
        id = Column('SQL_ID',BigInteger, primary_key=True)
        RefId = Column('REF_ID',Integer, ForeignKey('ORDERS.SQL_ID'))
        Type = Column("TYPE",String(3))
        Title = Column("TITLE",String(8))
        Name = Column("NAME",String(200,convert_unicode=True))
        CName = Column("CNAME",String(30))
        Additional = Column("ADDITIONAL",String(200,convert_unicode=True))
        Address = Column("ADDRESS",String(convert_unicode=True))
        City = Column("CITY",String(30))
        Zip = Column("ZIP",String(8))
        State = Column("STATE",String(30))
        Country = Column("COUNTRY",String(3))
        Postbox = Column("POBOX",Integer)
        AccountNo = Column("ACCOUNTNO",String(20))
    class OrderPosition(Table,BasicChangeableTable):
        __tablename__ = 'ORDERPOS'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        RefId = Column('REF_ID',Integer, ForeignKey('ORDERS.SQL_ID'))
        PosNo = Column("POSNO",Integer,nullable=False)
        PosTyp = Column("POSTYP",String(3))
        Active = Column("ACTIVE",String(1))
        TenderPosNo = Column("TPOSNO",String(15))
        Ident = Column("IDENT",String(20))
        Version = Column("VERSION",String(25))
        Language = Column("LANGUAGE",String(3))
        TextType = Column("TEXTTYPE",String(1))
        Shorttext = Column("SHORTTEXT",String(200,convert_unicode=True))
        Text = Column("TEXT",String(convert_unicode=True))
        Storage = Column("STORAGE",String(3))
        Serial = Column("SERIAL",String(20))
        Weight = Column("WEIGHT",Float)
        Avalible = Column("AVALIBLE",Float)
        Delivery = Column("DELIVERY",DateTime)
        Quantity = Column("QUANTITY",Float)
        QuantityDelivered = Column("QUANTITYD",Float)
        QuantityCalculated = Column("QUANTITYC",Float)
        QuantityO = Column("QUANTITYO",Float)
        QuantityUnit = Column("QUANTITYU",String(10))
        Purchase = Column("PURCHASE",Float)
        Sellprice = Column("SELLPRICE",Float)
        ComPrice = Column("COMPRICE",Float)
        Discount = Column("DISCOUNT",Float)
        Vat = Column("VAT",Integer)
        PosPrice = Column("POSPRICE",Float)
        GrossPrice = Column("GROSSPRICE",Float)
        Parent = Column("PARENT",Integer)
        ManufacNr = Column("MANUFACNR",String(40))
        RepairTime = Column("REPAIRTIME",Float)
        CostCentre = Column("COSTCENTRE",String(10))
        Account = Column("ACCOUNT",String(10))
        ProjectNr = Column("PROJECTNR",String(20))
        Script = Column("SCRIPT",String(60))
        ScriptVer = Column("SCRIPTVER",String(8))
        Plantime = Column("PLANTIME",Float)
        Time = Column("TIME",Float)
        Buffertime = Column("BUFFERTIME",Float)
        StartDate = Column("STARTDATE",DateTime)
        DueDate = Column("DUEDATE",DateTime)
        Earliest = Column("EARLIEST",DateTime)
        Latest = Column("LATEST",DateTime)
        SetupTime = Column("SETUPTIME",Float)
        PrepText = Column("PREPTEXT",String(100))
        WorkText = Column("WORKTEXT",String(100))
        PRScript = Column("PRSCRIPT",String(60))
        PRScriptVersion = Column("PRSCRIPTVER",String(8))
        ScriptFunc = Column("SCRIPTFUNC",String(60))
        PRScriptFunc = Column("PRSCRIPTFUNC",String(160))
        ImageRef = Column("IMAGEREF",Integer)
    class Order(Table,BasicChangeableTable):
        __tablename__ = 'ORDERS'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        OrderNo = Column('ORDERNO',Integer, nullable=False)
        Status = Column('STATUS',String(3), nullable=False)
        Language = Column('LANGUAGE',String(3))
        Date = Column('DATE',DateTime)
        Number = Column('NUMBER',String(20))
        CustNo = Column('CUSTNO', String(20))
        CustName = Column("CUSTNAME",String(200,convert_unicode=True))
        DateQuery = Column("DOAFQ",DateTime)
        DateWish = Column("DWISH",DateTime)
        DateApproved = Column("DAPPR",DateTime)
        DateFixed = Column("ODATE",DateTime)
        Storage=Column("STORAGE",String(3))
        Currency = Column("CURRENCY",String(5))
        PaymentTarget=Column("PAYMENTTAR",String(2))
        Shipping=Column("SHIPPING",String(3))
        ShippinngDate=Column("SHIPPINGD" ,DateTime)
        Weight=Column("WEIGHT",Float)
        VatHalf=Column("VATH",Float)
        VatFull=Column("VATF" ,Float)
        Netprice=Column("NETPRICE" ,Float)
        DiscountPrice=Column("DISCPRICE" ,Float)
        Discount=Column("DISCOUNT" ,Float)
        GrossPrice=Column("GROSSPRICE" ,Float)
        Done=Column("DONE",String(1))
        Delivered=Column("DELIVERED",String(1))
        PayedOn=Column("PAYEDON" ,DateTime)
        DeliveredOn=Column("DELIVEREDON" ,DateTime)
        Commission=Column("COMMISSION",String(30))
        Note=Column("NOTE",String)
        HeaderText=Column("HEADERTEXT",String)
        FooterText=Column("FOOTERTEXT",String)
        ProductID=Column("PID",String(250))
        Active=Column("ACTIVE",String(1))
        ProjectId=Column("PROJECTID",Integer)
        Project=Column("PROJECT",String(260))
        ProjectNr=Column("PROJECTNR",String(20))
        ProductVersion=Column("PVERSION",String(8))
        ProductLanguage=Column("PLANGUAGE",String(4))
        ProductQuantity=Column("PQUATITY" ,Float)
        CustomerZip=Column("CUSTZIP",String(8))
        CustomerEmail=Column("EMAIL",String(200))
        Addresses = relationship(OrderAddress, lazy='joined')
        Positions = relationship(OrderPosition, lazy='joined', order_by="OrderPosition.PosNo")
    class MasterdataPosition(Table,BasicChangeableTable):
        __tablename__ = 'MDPOSITIONS'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        RefId = Column('REF_ID',Integer, ForeignKey('MASTERDATA.SQL_ID'))
        PosNo = Column("POSNO",Integer,nullable=False)
        PosTyp = Column("POSTYP",String(3))
        Active = Column("ACTIVE",String(1))
        TenderPosNo = Column("TPOSNO",String(15))
        Ident = Column("IDENT",String(20))
        Version = Column("VERSION",String(25))
        Language = Column("LANGUAGE",String(3))
        TextType = Column("TEXTTYPE",String(1))
        Shorttext = Column("SHORTTEXT",String(200,convert_unicode=True))
        Text = Column("TEXT",String(convert_unicode=True))
        Storage = Column("STORAGE",String(3))
        Serial = Column("SERIAL",String(20))
        Weight = Column("WEIGHT",Float)
        Avalible = Column("AVALIBLE",Float)
        Delivery = Column("DELIVERY",DateTime)
        Qualtity = Column("QUANTITY",Float)
        QuantityDelivered = Column("QUANTITYD",Float)
        QuantityCalculated = Column("QUANTITYC",Float)
        QuantityO = Column("QUANTITYO",Float)
        QuantityUnit = Column("QUANTITYU",String(10))
        Purchase = Column("PURCHASE",Float)
        Sellprice = Column("SELLPRICE",Float)
        ComPrice = Column("COMPRICE",Float)
        Discount = Column("DISCOUNT",Float)
        Vat = Column("VAT",Integer)
        PosPrice = Column("POSPRICE",Float)
        GrossPrice = Column("GROSSPRICE",Float)
        Parent = Column("PARENT",Integer)
        ManufacNr = Column("MANUFACNR",String(40))
        RepairTime = Column("REPAIRTIME",Float)
        #CostCentre = Column("COSTCENTRE",String(10))
        #Account = Column("ACCOUNT",String(10))
        #ProjectNr = Column("PROJECTNR",String(20))
        Script = Column("SCRIPT",String(60))
        ScriptVer = Column("SCRIPTVER",String(8))
        Plantime = Column("PLANTIME",Float)
        Time = Column("TIME",Float)
        Buffertime = Column("BUFFERTIME",Float)
        StartDate = Column("STARTDATE",DateTime)
        DueDate = Column("DUEDATE",DateTime)
        Earliest = Column("EARLIEST",DateTime)
        Latest = Column("LATEST",DateTime)
        SetupTime = Column("SETUPTIME",Float)
        PrepText = Column("PREPTEXT",String(100))
        WorkText = Column("WORKTEXT",String(100))
        PRScript = Column("PRSCRIPT",String(60))
        PRScriptVersion = Column("PRSCRIPTVER",String(8))
        ScriptFunc = Column("SCRIPTFUNC",String(60))
        PRScriptFunc = Column("PRSCRIPTFUNC",String(160))
        ImageRef = Column("IMAGEREF",Integer)
    class Masterdata(Table,BasicChangeableTable):
        __tablename__ = 'MASTERDATA'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Type=Column("TYPE",String(1),nullable=False)
        Ident=Column("ID",String(40),nullable=False)
        Version=Column("VERSION",String(20))
        Language=Column("LANGUAGE",String(3))
        Status=Column("STATUS",String(3))
        Barcode=Column("BARCODE",String(20))
        MatchCode=Column("MATCHCODE",String(100))
        Shorttext=Column("SHORTTEXT",String(240))
        Treeentry=Column("TREEENTRY",Integer)
        QuantityUnit=Column("QUANTITYU",String(10))
        Var=Column("VAT",String(1))
        UseSerial=Column("USESERIAL",String(1))
        OwnProduction=Column("OWNPROD",String(1))
        Saleitem=Column("SALEITEM",String(1))
        NoStorage=Column("NOSTORAGE",String(1))
        PriceType=Column("PTYPE",String(1))
        Weight=Column("WEIGHT",Float)
        Unit=Column("UNIT",Integer)
        Warrenty=Column("WARRENTY",String(10))
        ManufacNumber=Column("MANUFACNR",String(20))
        ValidFrom=Column("VALIDFROM",DateTime)
        ValidTo=Column("VALIDTO",DateTime)
        ValidToMe=Column("VALIDTOME",Integer)
        CostCentre=Column("COSTCENTRE",String(10))
        Account=Column("ACCOUNT",String(10))
        CrDate=Column("CRDATE",DateTime)
        ChDate=Column("CHDATE",DateTime)
        Active=Column("ACTIVE",String(1))
        Currency=Column("CURRENCY",String(5))
        Category=Column("CATEGORY",String(60))
        #UPlace=Column("UPLACE",String(100))
        #UBuild=Column("UBUILD",DateTime)
        #USelbst=Column("USELBST",String(1))
        #UResponsible=Column("URESPONSEABLE",String(100))
        UseBatch=Column("USEBATCH",String(1))
        AccountingInfo=Column("ACCOUNTINGINFO",String)
        RepairTime=Column("REPAIRTIME",Integer)
        IsTemplate=Column("ISTEMPLATE",String(1))
        Sellprice=Column("SELLPRICE",Float)
        Purchase=Column("PURCHASE",Float)
        Script=Column("SCRIPT",String(60))
        ScriptVer=Column("SCRIPTVER",String(8))
        PrepText=Column("PREPTEXT",String(100))
        WorkText=Column("WORKTEXT",String(100))
        DispoType=Column("DISPOTYPE",String(1))
        PrScript=Column("PRSCRIPT",String(60))
        PrScriptVer=Column("PRSCRIPTVER",String(8))
        ScriptFunc=Column("SCRIPTFUNC",String(60))
        PRScriptFunc=Column("PRSCRIPTFUNC",String(160))
        ImageRef=Column("IMAGEREF",Integer)
        Positions = relationship(MasterdataPosition, lazy='joined')
    class Scripts(Table,TimestampTable):
        __tablename__ = 'SCRIPTS'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Type=Column("TYPE",String(1),nullable=False)
        Parent = Column('PARENT',Integer)
        Name=Column("NAME",String(60),nullable=False)
        Syntax=Column("SYNTAX",String(15),nullable=False)
        Script=Column("SCRIPT",String)
        Status=Column("STATUS",String(3))
        RunEvery = Column("RUNEVERY",Integer)
        Lastrun=Column("LASTRUN",DateTime)
        LastResult=Column("LASTRESULT",String)
        RunMashine=Column("RUNMASHINE",String)
        RunOnHistory=Column("RUNONHISTORY",String(1))
        FoldState=Column("FOLDSTATE",String(200))
        Note=Column("NOTE",String)
        Version=Column("VERSION",String(25))
        Active=Column("ACTIVE",String(1))
        Priority = Column("PRIORITY",Integer)
    class Boilerplate(Table,TimestampTable):
        __tablename__ = 'BOILERPLATE'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Name=Column("NAME",String(100,convert_unicode=True),nullable=False)
        Text=Column("TEXT",String(convert_unicode=True))
    class NumberRange(Table,BasicCreateableTable):
        __tablename__ = 'NUMBERRANGES'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Tablename=Column("TABLENAME",String(25,convert_unicode=True),nullable=False)#Numberset
        Pool=Column("POOL",String(25,convert_unicode=True))#Numberpool
        Start=Column("START",BigInteger,nullable=False)
        Stop=Column("STOP",BigInteger,nullable=False)
        Use=Column("USE",String(200,convert_unicode=True))
        Notice=Column("NOTICE",String(convert_unicode=True))
    class PasswordSave(Table,TimestampTable):
        __tablename__ = 'PWSAVE'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Name=Column("NAME",String(200,convert_unicode=True))
        Site=Column("SITE",String(500,convert_unicode=True))
        UserName=Column("USERNAME",String(400,convert_unicode=True))
        Password=Column("PASSWORD",String(400,convert_unicode=True))
        Date=Column("DATE",DateTime)
def GetID(session):
    nid = None
    try:
        c = session.query(IDGenerator).first()
        nid = c.gid
        stmt = update(IDGenerator).values(gid=nid+1)
        session.execute(stmt)
        session.commit()
    except TableException as e:
        logging.error(str(e))
        nid=None
    return nid
def GetConfigPath(appname='prometerp'):
    if 'APPDATA' in os.environ:
        confighome = os.environ['APPDATA']
    elif 'XDG_CONFIG_HOME' in os.environ:
        confighome = os.environ['XDG_CONFIG_HOME']
    else:
        confighome = os.path.join(os.environ['HOME'])
        if appname[:1] != '.':
            appname = '.'+appname
    return os.path.join(confighome, appname)
def GetConnection(ConnStr=None,Mandant=None):
    if not ConnStr:
        if not Mandant:
            mc = 0
            for connFile in pathlib.Path(GetConfigPath()).glob('*.perml'):
                mc += 1
            if mc == 1:
                Mandant = os.path.basename(connFile)[:-6]
        if Mandant:
            with open(str(pathlib.Path(GetConfigPath()) / (Mandant+'.perml')),'r') as f:
                tmp = f.readline()
                if tmp.startswith('SQL'):
                    tmp = f.readline().replace('\n','').split(';')
                if ':' in tmp[1]:
                    aport = tmp[1].split(':')[1]
                    ahost = tmp[1].split(':')[0]
                else:
                    aport = '5433'
                    ahost = tmp[1]
                apasswd = tmp[4]
                if apasswd[:1] == 'x':
                    logging.warning('Unsupported password encryption')
                    return None #encryptedt passwd
                if tmp[0].startswith('postgresql'):
                    ConnStr = 'postgresql+psycopg2://%s:%s@/%s?host=%s&port=%s' % (tmp[3],urllib.parse.quote_plus(apasswd),tmp[2],ahost,aport)
    if not ConnStr:
        raise Exception('No Mandant Configuration found')
    try:
        if logging.root.level == logging.DEBUG:
            engine = create_engine(ConnStr, echo=True)
        else:
            engine = create_engine(ConnStr)
        engine.convert_unicode = True
        Table.metadata.create_all(engine)
        if engine:
            Session = sessionmaker(bind=engine)
            session = Session()
    except BaseException as e:
        logging.warning(str(e))
        return None
    return session
import re,json
def dumps_compact(*sub, **kw):
    non_space_pattern = re.compile('[^ ]')
    compact_length = kw.pop('compact_length', None)
    r = json.dumps(*sub, **kw)
    r = r.replace(']',']\n')
    r = r.replace('[','[\n ')
    r = r.replace('},','},\n')
    return r