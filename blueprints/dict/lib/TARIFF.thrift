namespace java ru.korus.tmis.tariff.thriftgen
//Namespace=package name for java

typedef i32 int
typedef i64 timestamp
typedef i16 tinyint

struct Tariff{
	1:required int number;
	2:required string c_tar;
	3:required double summ_tar;
	4:required timestamp date_b;
	5:required timestamp date_e;
}

struct Error{
    1:required tinyint code;
    2:required string message;
}

struct Result{
    1:required int number;
	2:required string c_tar;
	3:optional Error error;
}

//Exceptions
exception SQLException{
	1:string message;
	2:int code;
}

exception InvalidArgumentException{
	1:string message;
	2:int code;
}

service TARIFFService{

    //Загрузка тарифов
    list<Result> updateTariffs(
            1:list<Tariff> tariffs,
            2:int contract_id
        )
        throws (1:InvalidArgumentException argExc, 2:SQLException sqlExc);
}