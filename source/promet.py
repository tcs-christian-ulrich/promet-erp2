import logging,warnings,sys,pathlib,os
from typing import Text
from sqlalchemy import Column, ForeignKey, Integer, BigInteger, String, func, update
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import relation, relationship, sessionmaker
from sqlalchemy.sql.sqltypes import DateTime, Float
import json,tojson,threading,urllib.parse
Base = declarative_base()
session = None
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    class IDGenerator(Base):
        __tablename__ = 'GEN_SQL_ID'
        #id = Column('SQL_ID',BigInteger, primary_key=True, autoincrement=True)
        gid = Column('ID',BigInteger, primary_key=True)
    class User(Base):
        __tablename__ = 'USERS'
        id = Column('SQL_ID',BigInteger, primary_key=True)
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
    class OrderAddress(Base,tojson.OutputMixin):
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
        TimestampD = Column("TIMESTAMPD",DateTime)
    class OrderPosition(Base,tojson.OutputMixin):
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
        TimestampD = Column("TIMESTAMPD",DateTime)
        Parent = Column("PARENT",Integer)
        ChangedBy = Column("CHANGEDBY",String(4))
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
        CreatedBy = Column("CREATEDBY",String(4))
        ScriptFunc = Column("SCRIPTFUNC",String(60))
        PRScriptFunc = Column("PRSCRIPTFUNC",String(160))
        ImageRef = Column("IMAGEREF",Integer)
    class Order(Base,tojson.OutputMixin):
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
        CreatedBy=Column("CREATEDBY",String(4))
        TimestampD=Column("TIMESTAMPD",DateTime,nullable=False)
        ProductID=Column("PID",String(250))
        ChangedBy=Column("CHANGEDBY",String(4))
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
    class MasterdataPosition(Base,tojson.OutputMixin):
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
        TimestampD = Column("TIMESTAMPD",DateTime)
        Parent = Column("PARENT",Integer)
        ChangedBy = Column("CHANGEDBY",String(4))
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
        CreatedBy = Column("CREATEDBY",String(4))
        ScriptFunc = Column("SCRIPTFUNC",String(60))
        PRScriptFunc = Column("PRSCRIPTFUNC",String(160))
        ImageRef = Column("IMAGEREF",Integer)
    class Masterdata(Base,tojson.OutputMixin):
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
        ChangedBy=Column("CHANGEDBY",String(4))
        CreatedBy=Column("CREATEDBY",String(4))
        Active=Column("ACTIVE",String(1))
        TimestampD=Column("TIMESTAMPD",DateTime,nullable=False)
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
    class Scripts(Base,tojson.OutputMixin):
        __tablename__ = 'SCRIPTS'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Type=Column("TYPE",String(1),nullable=False)
        Parent = Column('PARENT',Integer)
        Name=Column("NAME",String(60),nullable=False)
        Syntax=Column("SYNTAX",String(15),nullable=False)
        Script=Column("SCRIPT",String)
        TimestampD=Column("TIMESTAMPD",DateTime,nullable=False)
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
    class Boilerplate(Base,tojson.OutputMixin):
        __tablename__ = 'BOILERPLATE'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Name=Column("NAME",String(100,convert_unicode=True),nullable=False)
        Text=Column("TEXT",String(convert_unicode=True))
    class NumberRange(Base,tojson.OutputMixin):
        __tablename__ = 'NUMBERRANGES'
        RELATIONSHIPS_TO_DICT = True
        id = Column('SQL_ID',BigInteger, primary_key=True)
        Tablename=Column("TABLENAME",String(25,convert_unicode=True),nullable=False)#Numberset
        Pool=Column("POOL",String(25,convert_unicode=True))#Numberpool
        Start=Column("START",BigInteger,nullable=False)
        Stop=Column("STOP",BigInteger,nullable=False)
        Use=Column("USE",String(200,convert_unicode=True))
        Notice=Column("NOTICE",String(convert_unicode=True))
        CreatedBy=Column("CREATEDBY",String(4,convert_unicode=True))
        TimestampD=Column("TIMESTAMPD",DateTime,nullable=False)
def GetID(session):
    nid = None
    try:
        c = session.query(IDGenerator).first()
        nid = c.gid
        stmt = update(IDGenerator).values(gid=nid+1)
        session.execute(stmt)
        session.commit()
    except BaseException as e:
        logging.error(str(e))
        nid=None
    return nid
def GetConfigPath(appname='prometerp'):
    if 'APPDATA' in os.environ:
        confighome = os.environ['APPDATA']
    elif 'XDG_CONFIG_HOME' in os.environ:
        confighome = os.environ['XDG_CONFIG_HOME']
    else:
        confighome = os.path.join(os.environ['HOME'], '.config')
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
                    return None #encryptedt passwd
                if tmp[0].startswith('postgresql'):
                    ConnStr = 'postgresql+psycopg2://%s:%s@/%s?host=%s&port=%s' % (tmp[3],urllib.parse.quote_plus(apasswd),tmp[2],ahost,aport)
    try:
        if logging.root.level == logging.DEBUG:
            engine = create_engine(ConnStr, echo=True, echo_pool='debug')
        else:
            engine = create_engine(ConnStr, echo=True, echo_pool='debug')
        engine.convert_unicode = True
        Base.metadata.create_all(engine)
        if engine:
            Session = sessionmaker(bind=engine)
            session = Session()
    except BaseException as e:
        logging.warning(str(e))
        return None
    return session