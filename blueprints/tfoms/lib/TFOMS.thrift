namespace java ru.korus.tmis.tfoms.thriftgen
//Namespace=package name for java

/**
 * Список используемых сокращений и аббревиатур
 * СМО - Страховая Медицинская Организация
 * ОКАТО - Общероссийский Классификатор Административно-Территориальных Объектов
 * ОГРН - Основной Государственный Регистрационный Номер
 * ЛПУ - Лечебно-Профилактичесое Учреждение
*/

// Переопределения типов
typedef i32 int
typedef i64 timestamp
typedef i16 tinyint

//OUTPUT STRUCTURES
/**
 * Представитель пациента
 * @param patientId         1)Идентификатор пациента
 * @param FAM_P             2)Фамилия
 * @param IM_P              3)Имя
 * @param OT_P              4)Отчество
 * @param DR_P              5)Дата рождения
 * @param W_P               6)Пол
 */
struct Spokesman{
	1:optional int patientId;
	2:optional string FAM_P;
	3:optional string IM_P;
	4:optional string OT_P;
	5:optional timestamp DR_P;
	6:optional tinyint W_P;
}

/**
 * Person
 * Данные о пациенте
 * *****************
 * Данные для тега PERS  (Не зависящие от даты оказания услуги)
 * *********
 * @param patientId     внутренний идентфикатор пациента в БД ЛПУ
 * @param FAM       Фамилия пациента
 * @param IM        Имя пациента
 * @param OT        Отчество пациента
 * @param DR        Дата рождения пациента
 * @param W         Пол пациента
 * @param SNILS     Номер снилс
 * @param MR        Место рождения
 * @param OKATOP    адрес проживания
 * @param OKATOG    адрес регистрации
 * @param spokesman         Представитель пациента
 */
struct Person{
	1:required int patientId = -1; 	
	2:required string FAM;
	3:required string IM;
	4:required string OT;
	5:required timestamp DR;
	6:required tinyint W;
	7:optional string SNILS;
	8:optional string MR;
	9:optional string OKATOG;
	10:optional string OKATOP;
	11:optional Spokesman spokesman;
}

/**
 * Patient
 * Данные о пациенте
 * *****************
 * Данные для тега Pacient  (Зависящие от даты оказания услуги)
 * *********
 * @param patientId     внутренний идентфикатор пациента в БД ЛПУ
 * @param NOVOR         Признак новорожденного
 * @param DOCTYPE       Тип документа
 * @param DOCSER        Серия документа
 * @param DOCNUM        Номер документа
 * @param VPOLIS        Тип полиса
 * @param SPOLIS        Серия полиса
 * @param NPOLIS        Номер полиса
 * @param SMO           Инфис-код страховщика
 * @param SMO_OGRN      ОГРН страховщика
 * @param SMO_OK        Код окато страховщика
 * @param SMO_NAM       Полное наименование страховщика
 * @param VNOV_D    данные о весе ребенка при рождении (в случае оказания помощи маловесным и недоношенным детям)  Client.weight
 */
 struct Patient{
     1:required string NOVOR;
     2:optional string DOCTYPE;
     3:optional string DOCSER;
     4:optional string DOCNUM;
     5:required tinyint VPOLIS;
     6:optional string SPOLIS;
     7:required string NPOLIS;
     8:required string SMO;
     9:optional string SMO_OGRN;
     10:optional string SMO_OK;
     11:optional string SMO_NAM;
     12:optional int VNOV_D;
     //внутренний идентификатор пациентав БД ЛПУ
     13:optional int patientId;
 }

//Данные о услуге
struct Usl{
	1:required int IDSERV = -1;
	2:required string CODE_USL;
	3:required double KOL_USL;
	4:required double TARIF;
	//Внутренние идентификаторы
	5:required int contract_TariffId;
}
/**
 * Sluch
 * Структура с данными о случае оказания мед помощи
 * *******
 * @param IDCASE    Идентификатор выставленной позиции счета
 * @param USL_OK
 * @param VIDPOM
 * @param NPR_MO
 * @param EXTR
 * @param FOR_POM
        Данные о форме оказания помощи  (Event.order -> rbAppointmentOrder.id -> rbAppointmentOrder.TFOMScode_account)
                        Возможные значения:
                        1-плановая;
                        2-экстренная;
                        3-неотложная.
 * @param LPU
 * @param LPU_1
 * @param PODR
 * @param PROFIL
 * @param DET
 * @param NHISTORY
 * @param DATE_1
 * @param DATE_2
 * @param DS0
 * @param DS1
 * @param DS2
 * @param CODE_MES1
 * @param CODE_MES2
 * @param RSLT
 * @param ISHOD
 * @param PRVS
 * @param IDDOKT
 * @param OS_SLUCH
 * @param IDSP
 * @param
 * *******
*/
struct Sluch{
	1:required int IDCASE;
	2:required tinyint USL_OK;
	3:required tinyint VIDPOM;
	4:optional string NPR_MO;
	5:optional tinyint EXTR;
	6:required tinyint FOR_POM;
	7:required string LPU;
	8:optional string LPU_1;
	9:optional string PODR;
	10:required tinyint PROFIL;
	11:optional bool DET;
	12:required string NHISTORY;
	13:required timestamp DATE_1;
	14:required timestamp DATE_2;
	15:optional string DS0;
	16:optional string DS1;
	17:optional string DS2;
	18:optional string CODE_MES1;
	19:optional string CODE_MES2;
	20:required tinyint RSLT;
	21:required tinyint ISHOD;
	22:required int PRVS = -1;
	23:required string IDDOKT = "";
    24:optional list<int> OS_SLUCH;
	25:required tinyint IDSP;
	// параметры относящиеся больше к пациенту,
	26:required Patient patient;

	30:required double ED_COL;
	31:required double SUMV;

	32:required list<Usl> USL;
}

//Перечисление с названиями требуемых опциональных полей
enum PatientOptionalFields{
	// Тип документа пациента
	DOCTYPE,
	// Серия документа пациента
	DOCSER,
	// Номер документа пациента
	DOCNUM,
    // Серия полиса пациента
	SPOLIS,
	// ОГРН СМО
	SMO_OGRN,
	// Наименование СМО
	SMO_NAM,
	// Код ОКАТО территории страхования
	SMO_OK,
	// данные о весе ребенка при рождении (в случае оказания помощи маловесным и недоношенным детям)
	VNOV_D
}

enum PersonOptionalFields{
    // Снилс пациента
	SNILS,
	// Место рождения пациента
	MR,
	// Код ОКАТО адреса регистрации пациента
	OKATOG,
	// Код ОКАТО адреса  проживания пациента
	OKATOP,
	// Фамилия предствателя пациента
    FAM_P,
    // Имя представителя пациента
    IM_P,
    // Отчество представителя пациента
    OT_P,
    // Дата рождения представителя пациента
    DR_P,
    // Пол представителя пациента
    W_P
}

enum SluchOptionalFields{
	NPR_MO,
	EXTR,
	LPU_1,
	PODR,
	DET,
	DS0,
	DS2,
	CODE_MES1,
	CODE_MES2,
	OPLATA, 
	OS_SLUCH
}

//Структуры для загрузки из тфомс
struct TClientPolicy{
	1:required string serial;
	2:required string number;
	3:required tinyint policyTypeCode;
	4:optional timestamp begDate;
	5:optional timestamp endDate;
	6:optional string insurerInfisCode;
}
//Структуры для DBF
struct DBFStationary{
	1:required timestamp DAT_VV = 0;
	2:required timestamp DAT_PR = 0;
	3:required string SER_POL = "";
	4:required string NOM_POL = "";
	5:required string FAMIL = "";
	6:required string IMYA = "";
	7:required string OT = "";
	8:required string KOD_F = "";
	9:required string POL = "Н";
	10:required timestamp D_R = 0;
	11:required tinyint RAION = 0;
	12:required tinyint KOD_T = 0;
	13:required string NAS_P = "";
	14:required string UL = "";
	15:required string DOM = "";
	16:required string KV = "";
	17:required tinyint KATEGOR  = 2;
	18:required string MES_R = "Неработающий";
	19:required string KOD_PR = "Не заполняется";
	20:required tinyint OTD = 0;
	21:required string N_KART = "";
	22:required string DIA_O = "";
	23:required string DOP_D = "";
	24:required string DIA_S = ""; 
	25:required string DOP_S = ""; 
	26:required string DIA_S1 = "";  
	27:required string DOP_S1 = "";
	28:required string OSL = ""; 
	29:required string DOP_OSL = ""; 
	30:required string KSG_MS = "";  
	31:required tinyint DL_LEC = 0;
	32:required tinyint SL = 0;
	33:required tinyint ISH_LEC = 0;
	34:required tinyint PR_NZ = 0;
	35:required double STOIM = 0.0;
	36:required string KOD_VR = ""; 
	37:required string KOD_O = "Не заполняется";
	38:required string N_OPER = "Не заполняется"; 
	39:required int KOL_USL = 0; 
	//TODO Спросить почему не double
	40:required double Tarif = 0.0;
	41:required int KOD_TSK = 0;
	42:required string NAMCMO = "";
	43:required tinyint KOD_DOK = 0;
	44:required string SER_DOK = ""; 
	45:required string NOM_DOK = ""; 
	46:required tinyint VMP = 0;
	47:required timestamp DAT_BLVN = 0; 
	48:required timestamp DAT_ELVN = 0; 
	49:required bool DAMAGE = false;
	50:required timestamp DATA_NS = 0;
}

struct DBFPoliclinic{	 
	1:required timestamp DAT_VV = 0;
	2:required timestamp DAT_PR = 0;
	3:required string SER_POL = "";
	4:required string NOM_POL = "";
	5:required string SNILS = "";
	6:required string FAMIL = "";
	7:required string IMYA = "";		
	8:required string OT = "";
	9:required string KOD_F = "";
	10:required string POL = "Н";  
	11:required timestamp D_R = 0;
	12:required tinyint RAION = 0;
	13:required tinyint KOD_T = 0;
	14:required string NAS_P = "";
	15:required string UL = "";
	16:required string DOM = "";
	17:required string KV = "";
	18:required int KATEGOR = 1;
	19:required string MES_R = "Неработающий";
	20:required string KOD_PR = "Не заполняется";
	21:required tinyint OTD = 0;
	22:required string N_KART = "";
	23:required tinyint KC = 0;
	24:required string DIA_O = "";
	25:required string DOP_D = "";
	26:required string DIA_S = ""; 
	27:required string DOP_S = ""; 
	28:required string DIA_S1 = "";  
	29:required string DOP_S1 = "";
	30:required string OSL = "";  
	31:required string DOP_OSL = ""; 
	32:required string KSG_MS = "Не заполняется";  
	33:required tinyint DL_LEC = 0;
	34:required tinyint KOL_POS = 0;
	35:required tinyint POS_D = 0;
	36:required tinyint SL = 0;
	37:required tinyint ISH_LEC = 0;
	38:required tinyint PR_NZ = 0;
	39:required double STOIM = 0.0;
	40:required string KOD_VR = "";  
	41:required tinyint S_VR = 0;
	42:required string NOM_SL = "Не заполняется";    
	43:required string KOD_O = "Не заполняется";
	44:required string N_OPER = "Не заполняется"; 
	45:required int KOL_USL = 0; 
	//TODO -"-
	46:required tinyint KOD_TSK = 0;
	47:required string NAMCMO = ""; 
	48:required tinyint KOD_DOK = 0;
	49:required string SER_DOK = ""; 
	50:required string NOM_DOK = ""; 
	51:required tinyint VMP = 0;
	52:required timestamp DAT_BLVN = 0; 
	53:required timestamp DAT_ELVN = 0; 
	54:required bool DAMAGE = false;
	55:required timestamp DATA_NS = 0; 
}

/*
Структура счета
Поля:
    1-Внутренний идентификатор в БД ЛПУ
    2-Номер счета
    3-Дата формирования счета (createDateTime -time)
    4-Дата начала интервала за который оказывались услуги
    5-Дата конца интервала за который оказывались услуги
    6-Общее количество случаев в счете
    7-Общее количество УЕТ в счете
    8-Общая сумма все выствленных в счет услуг
    9-Дата отправки счета в ТФОМС
    10-Число оплаченных позиции счета
    11-Сумма оплаченых услуг
    12-Число отказаных в оплате позиций
    13-Сумма всех отказанных в оплате услуг
    14- идентификатор контракта для этого счета
*/
struct Account{
    1:required int id;
    2:required string number;
    3:required timestamp date;
    4:required timestamp begDate;
    5:required timestamp endDate;
    6:required int amount;
    7:required double uet;
    8:required double sum;
    9:optional timestamp exposeDate;
    10:required int payedAmount;
    11:required double payedSum;
    12:required int refusedAmount;
    13:required double refusedSum;
    14:required int contractId;
}

/*
Структура позиции счета
Поля:
    1- Внутренний идентификатор в БД ЛПУ
    2- дата оказания услуги
    3- Фамилия пациента, которому оказывалась услуга
    4- Имя пациента
    5- Отчество пациента
    6- пол пациента
    7- Дата рождения пациента
    8- Общая сумма за услугу
    9- Количество оказанных услуг
    10- Название единицы учета услуги
    11- дата загрузки результата из ТФОМС
    12- имя файла, загруженного из тфомс
    13- наименование причины отказа от оплаты
    14- код причины отказа от оплаты
    15- Примечание (SLUCH:COMENT_USL)
*/
struct AccountItem{
    1:required int id;
    2:required timestamp serviceDate;
    3:required string lastName;
    4:required string firstName;
    5:required string patrName;
    6:required tinyint sex;
    7:required timestamp birthDate;
    8:required double price;
    9:required double amount;
    10:required string unitName;
    11:optional timestamp date;
    12:required string fileName;
    13:optional string refuseTypeName;
    14:optional tinyint refuseTypeCode;
    15:optional string note;
    16:optional bool doNotUploadAnymore;
}

/**
 * AccountInfo
 * Структура с данными о счете и его позициях
 * @param account Вложенная структура с данными о счете
 * @param items  Список вложенных структур с данными о позициях счета
*/
struct AccountInfo {
    1:required Account account;
    2:required list<AccountItem> items;
}

/**
 * AccountItemWithMark
 * Структура с данными о позиции счета которой нужно поменять флаг "не выгружать более"
 * @param id                            1) Уникальный идетификатор позиции счета (AccountItem.id)
 * @param status                        2) true - Выставить отметку "Не выгружать более" \ false - снять отметку "не выгружать более"
 * @param note                          3) примичание к изменению отметки
 */
 struct AccountItemWithMark{
    1:required int id;
    2:required bool status;
    3:optional string note;
 }

/**
 * Структура с данными об оплате выгруженного случая
 * @param accountItemId                1)Уникальный идентификатор позиции счета (SLUCH:IDCASE)
 * @param refuseTypeCode               2)Код причины отказа в оплате            (SLUCH:REFREASON)
 * @param comment                      3)Комментарий к оплате случая            (SLUCH:COMENTSL)
 */
struct Payment{
    1:required int accountItemId;
    2:optional string refuseTypeCode;
    3:optional string comment;
}

/*
Структура подразделения ЛПУ
Поля:
    1- Внутренний идентификатор в БД ЛПУ
    2- код подразделения
    3- наименование подразделения
    4- Идентификатор родительского подразделения
    5- Тип подразделения (0-амбулатория,1-дневной стационар,2-скорая,3-мобильная станция,4-приемное отделение стационара,5-круглосуточный стационар)
*/
struct OrgStructure{
    1:required int id;
    2:required string code;
    3:required string name;
    4:optional int parentId;
    5:optional int type;
}
/*
Структура контрактов
Поля:
    1- Внутренний идентификатор в БД ЛПУ
    2- номер договора
    3- дата начала действия контракта
    4- дата конца действия контракта
    5- Постановление (основание договора)
*/
struct Contract{
    1:required int id;
    2:required string number;
    3:required timestamp begDate;
    4:required timestamp endDate;
    5:required string resolution;
}

/*
Структура счета (для тега SCHET)
Поля:
    1- Код записи счета
    2- Реестровый номер медицинской организации
    3- Отчетный год
    4- Отчетный месяц
    5- Номер счёта	Формат YYMM-N/ Ni
    6- Дата выставления счёта
    7- Плательщик. Реестровый номер СМО.
    8- Сумма МО, выставленная на оплату
    9- Служебное поле к счету
    10- Сумма, принятая к оплате СМО (ТФОМС)
    11- Финансовые санкции (МЭК)
    12- Финансовые санкции (МЭЭ)
    13- Финансовые санкции (ЭКМП)
*/
struct Schet{
    1:required tinyint CODE;
    2:required string CODE_MO;
    3:required tinyint YEAR;
    4:required tinyint MONTH;
    5:required string NSCHET;
    6:required timestamp DSCHET;
    7:optional string PLAT;
    8:required double SUMMAV;
    9:optional string COMENTS;
    10:optional double SUMMAP;
    11:optional double SANK_MEK;
    12:optional double SANK_MEE;
    13:optional double SANK_EKMP;
}

/*
 Структура ответа на запрос по получению реестров
 Поля:
     1- Сформированный счет в БД
     2- Реестры в виде (Пациент- Список его случаев)
     3- Дата формирования реестра
     4- Имя файла реестра пациентов
     5- Имя файла реестра услуг
     6- Набор значений для тега SCHET
     7- Значение тега PR_NOV, которое будет выставляться во все ZAP в итоговом XML-файле
*/
struct XMLRegisters{
    1:required Account account;
    2:required map<Person, list<Sluch>> registry;
    3:required timestamp data;
    4:required string patientRegistryFILENAME;
    5:required string serviceRegistryFILENAME;
    6:required Schet schet;
    7:required i16 PR_NOV;
}

//Exceptions
exception NotFoundException{
	1:string message;
	2:int code;
}

exception SQLException{
	1:string message;
	2:int code;
}

exception InvalidArgumentException{
	1:string message;
	2:int code;
}

exception InvalidOrganizationInfisException{
    1:string message;
    2:int code;
}

exception InvalidContractException{
     1:string message;
     2:int code;
}

exception InvalidDateIntervalException{
     1:string message;
     2:int code;
}

//Сервис для работы с ТФОМС
service TFOMSService{

//Работа со счетами
    /**
     * Получение всех доступных счетов (deleted = 0), в случае если счетов нету - пустой сисок.
     * @return список счетов
     */
    list<Account> getAvailableAccounts();

    /**
     * Получение одного счета по его идентификатору
     * @param accountId : идентификатор счета
     * @throw NotFoundException nfExc : Если нету счета с таким идентификатором
     * @return Счет / Ошибка
     */
    Account getAccount(1:int accountId) throws (1:NotFoundException nfExc);

    /**
     * Получение всех позиций счета по идентификатору счета
     * @param accountId : идентификатор счета по которому будут возвращены позиции
     * @throw NotFoundException nfExc : Если нету счета с таким идентификатором
     * @return Список позиций счета или пустой список если на счет нету ни одной позиции
     */
    AccountInfo getAccountItems(1:int accountId) throws (1:NotFoundException nfExc);

    /**
    * Проставление отметки "не выгружать более" для заданных позиций счета
    * @param items Список структур позиций счета, которых более не требуется выгружать ни в одном счете
    */
    oneway void setDoNotUploadAnymoreMarks(1:list<AccountItemWithMark> items);

    /*
        Удаление счета
        Arguments:
        1 -  int accountId : идентификатор счета который планируется удалить
        Return:
        True - удаление успешно \ False - удаление не удалось
    */
    bool deleteAccount(1:int accountId);

//Выгрузка в формате XML
	/*
	    Получение реестров по заданным параметрам
	    Arguments:
	    1 -  int contractId : Идентификатор контракта
	    2 -  timestamp beginDate : начало интервала за который формируется реестр
	    3 -  timestamp endDate : конец интервала за который формируется реестр
	    4 -  string infisCode : Инфис код ЛПУ
	    5 -  string obsoleteInfisCode : Старый инфис-код
	    6 -  string smoNumber : Номер области СМО
	    7 -  list<int> orgStructureIdList : Список подразделений
	    8 -  set<PatientOptionalFields> patientOptionalFields : перечень требуемых опциональных полей структуры PACIENT
	    9 -  set<PersonOptionalFields> personOptionalFields : перечень опциональных полей структуры PERS
	    10 -  set<SluchOptionalFields> sluchOptionalFields : перечень требуемых опциональных полей реестра услуг
	    11 -  bool primaryAccount : признак первичного \ повторного счета
	    12 - string levelMO : Строка с уровнем МО (WMIS-66)
	    Exceptions:
	    1 - InvalidOrganizationInfisException : нету организации с таким инфис-кодом
	    2 - InvalidContractException : нету контракта с таким идентификатором
	    3 - InvalidDateIntervalException : некорректный диапозон дат
	    4 - InvalidArgumentException : некорректное значение параметра   9(primaryAccount)
	    5 - NotFoundException : не найдено ни одной оказанной услуги
	    6 - SQLException : ошибка при обращении к БД
	    Return:
	    XMLRegisters - набор реестров и заголовок
	*/
	XMLRegisters getXMLRegisters(
            1:int contractId,
            2:timestamp beginDate,
            3:timestamp endDate,
            4:string infisCode,
            5:string obsoleteInfisCode,
            6:string smoNumber,
            7:list<int> orgStructureIdList,
            8:set<PatientOptionalFields> patientOptionalFields,
            9:set<PersonOptionalFields> personOptionalFields,
            10:set<SluchOptionalFields> sluchOptionalFields,
            11:bool primaryAccount,
            12:string levelMO
            )
        throws (
            1:InvalidOrganizationInfisException infisExc,
            2:InvalidContractException contractExc,
            3:InvalidDateIntervalException datesExc,
            4:InvalidArgumentException invExc,
            5:NotFoundException nfExc,
            6:SQLException sqlExc
            );

//Работа с подразделениями ЛПУ
    /**
     * Получение всех подразделений у которых  инфис-код ЛПУ совпадает с заданным
     * @param organisationInfis             1)Инфис код ЛПУ для которого необходимо вернуть подразделения
     * @throw InvalidOrganizationInfisException  когда нету организации с таким инфис-кодом
     */
    list<OrgStructure> getOrgStructures(1:string organisationInfis)
        throws (1:InvalidOrganizationInfisException infisExc);

//Работа с контрактами
    /**
     * Получение всех контрактов, где получателем является заданное ЛПУ
     * @param organisationInfis            1)Инфис код ЛПУ для которого необходимо вернуть контракту
     * @throw InvalidOrganizationInfisException  когда нету организации с таким инфис-кодом
     */
    list<Contract> getAvailableContracts(1:string organisationInfis)
        throws (1:InvalidOrganizationInfisException infisExc);

//Работа с ответом из тфомса
	/**
	 * Загрузка измененных данных от ТФОМС
	 */
	int changeClientPolicy(1:int patientId, 2:TClientPolicy newPolicy)  
		throws (1:InvalidArgumentException argExc, 2:SQLException sqlExc);

	/**
	 * загрузка результатов оплаты случаев из ТФОМС
	 * @param fileName имя файла в котором содержатся результаты ответа из ТФОМС
	 * @param payments список структур с данными об оплате случая
	 * @param refusedAmount количество отказанных случаев
	 * @param payedAmount количество оплаченных случаев
	 * @param payedSum  оплаченная сумма
	 * @param refusedSum отказнная в оплате сумма
	 * @param accountNumber номер счета
	 * @param comment   комментарий к счету
	 * @return map<int, string> карта вида <идентификатор позиции счета, текст ошибки>
	 * или пустой список если все ок
	 * @throw  NotFoundException когда в БД ЛПУ нету счета с таким номером
	 */
	map<int, string> loadTfomsPayments( 1:string fileName,
                                        2:list<Payment> payments,
                                        3:int refusedAmount,
                                        4:int payedAmount,
                                        5:double payedSum,
                                        6:double refusedSum,
                                        7:string accountNumber,
                                        8:string comment
    ) throws (1:NotFoundException nfExc);


	//Выгрузка в формате DBF
	//list<DBFStationary> getDBFStationary(
    //			1:timestamp beginDate,
    //			2:timestamp endDate,
    //			3:string infisCode
    //			)
    //		throws (1:InvalidArgumentException argExc, 2:SQLException sqlExc, 3:NotFoundException exc);
    //
    //	list<DBFPoliclinic> getDBFPoliclinic(
    //			1:timestamp beginDate,
    //			2:timestamp endDate,
    //			3:string infisCode
    //			)
    //		throws (1:InvalidArgumentException argExc, 2:SQLException sqlExc, 3:NotFoundException exc);
}