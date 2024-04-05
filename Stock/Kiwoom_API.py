import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3

TR_REQ_TIME_INTERVAL = 0.2

ETF = 8


class Kiwoom(QAxWidget):
    # 클래스 호출 시 실행
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    # 키움오픈API 연결
    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    # 신호 생성
    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)  # 연결 이벤트가 발생하면 _event_connect 함수 호출
        self.OnReceiveTrData.connect(self._receive_tr_data)  # 발생시킨 TR data에 대한 응답이 오면 _receive_tr_data 함수 호출
        self.OnReceiveChejanData.connect(self._receive_chejan_data)  # OnReceiveChejanData 이벤트를 처리
        # self.OnReceiveRealData.connect(self._receive_real_data) # OnReceiveRealData 이벤트를 처리

    # SetInputValue 메서드를 dynamicCall 메서드를 통해 호출하는 역할을 수행함
    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    # CommRqData메서드를 호출하는 코드와 QEventLoop 클래스의 인스턴스를 생성 후 이벤트 루프를 만들어줌
    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    # 실시간 조회용 테스트
    def get_comm_real_data(self, code, fid):
        self.dynamicCall("GetCommRealData(QString, int)", code, 10)
        print(code)
        self.real_event_loop = QEventLoop()
        self.real_event_loop.exec_()

    # OnReceiveRealData 이벤트 발생 시 호출되는 함수
    def _receive_real_data(self, code, type, data):
        print(code)
        print(type)
        print(data)
        # price = self.get_real_data(10)
        # print(price)
        return

    # 로그인 이벤트 발생
    def comm_connect(self):
        loginwindows = self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()
        return loginwindows

    # 연결상태를 표기
    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")
        self.login_event_loop.exit()  # 로그인 이벤트 시 발생시켰던 loop 종료

    # 시장구분에 따른 종목코드를 반환 0: 장내, 10: 코스닥, 8: ETF, 3:ELW (그외는 키움API 가이드 참조)
    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    # 종목코드의 한글명을 반환
    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    # 현재 연결상태 확인
    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    # 계좌정보 및 로그인 사용자 정보를 얻어오는 매서드 호출
    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    # TR처리에 대한 이벤트가 발생했을때 데이터 가져오기
    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        # print("commgetdata", code , real_type, field_name, index, item_name)
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code, real_type, field_name,
                               index, item_name)
        return ret.strip()

    # 반환되는 데이터의 수량을 확인하기 위해 GetRepeatCnt 함수 호출
    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    # 매수 주문, 체결이벤트 처리, 체결정보 획득
    # send_order 메서드 추가
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        ret = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                               [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
        return ret

    # OnReceiveChejanData 이벤트 발생할때 호출되는 함수
    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        order_no = self.get_chejan_data(9203)
        stock_name = self.get_chejan_data(302)
        order_num = self.get_chejan_data(900)
        order_price = self.get_chejan_data(901)
        print(gubun, order_no, stock_name, order_num, order_price)

    # 체결 잔고 데이터를 가져옴
    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    # 실시간 데이터를 가져옴
    def get_real_data(self, code, fid):
        ret = self.dynamicCall("GetCommRealData(int)", fid)
        return ret

    # 실 서버인지 모의투자 서버인지 구분
    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    # 숫자 왼쪽의 +,-,0을 제외하고, 천의 자리마다 콤마를 추가, 마지막에는 음수값 표현하여 리턴
    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-+0')
        if strip_data == '':
            strip_data = '0'

        try:
            format_data = format(int(strip_data), ',d')
        except:
            format_data = format(float(strip_data))

        if data.startswith('-'):
            format_data = '-' + format_data

        return format_data

    # 숫자 왼쪽의 -,0을 제외하고, 소수점으로 시작하는 경우에는 앞에 0을 붙임. 음수값인 경우 표현하고, 백분율로 리턴
    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'
        if strip_data.startswith('.'):
            strip_data = '0' + strip_data
        if data.startswith('-'):
            strip_data = '-' + strip_data
        strip_data = str(int(strip_data) / 100)
        return strip_data

    # CommRqData 후 이벤트가 발생했을 때 처리해주는 메서드
    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':  # 연속조회가 필요한 경우 PrevNext값을 2로 리턴하므로, 해당값을 보고 TR을 한번더 요청하여 데이터 획득
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":  # 주식일봉조회
            self._opt10081(rqname, trcode)
        elif rqname == "opt10001_req":  # 주식기본정보요청
            self._opt10001(rqname, trcode)
        elif rqname == "opt10007_req":  # 시세표성정보요청
            self._opt10007(rqname, trcode)
        elif rqname == "opw00001_req":  # 추정예수금 정보 확인
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":  # 계좌에 대한 정보 확인
            self._opw00018(rqname, trcode)
        elif rqname == "opt10004_req":  # 현재 매수/매도 호가 확인
            self._opt10004(rqname, trcode)
        elif rqname == "opt10080_req":  # 분봉정보 확인
            self._opt10080(rqname, trcode)
        elif rqname == "opt10087_req":  # 시간외단일가 요청에 대한 응답
            self._opt10087(rqname, trcode)
        elif rqname == "opt10012_req":  # 주문체결요청에 대한 응답
            self._opt10012(rqname, trcode)
        elif rqname == "send_order_req":
            print("Send Order")

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    ########################### 상황별 호출 함수 #####################################################################
    # 계좌예수금 확인
    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    def reset_opt10001_output(self):
        self.open_price = 0
        self.current_price = 0

    # 주식기본정보요청
    def _opt10001(self, rqname, trcode):
        open_price = self._comm_get_data(trcode, "", rqname, 0, "시가")
        current_price = self._comm_get_data(trcode, "", rqname, 0, "현재가")
        self.open_price = open_price.lstrip('+-')  # 앞의 부호 제거
        self.current_price = current_price.lstrip('+-')
        return 0

    # 시세표성정보요청
    def _opt10007(self, rqname, trcode):
        pre_price = self._comm_get_data(trcode, "", rqname, 0, "전일종가")
        self.pre_price = pre_price.lstrip('+-')  # 앞의 부호 제거
        return 0

    # 주식일봉조회
    def _opt10081(self, rqname, trcode):  # opt10081에 대한 답변을 함수로 호출
        data_cnt = self._get_repeat_cnt(trcode, rqname)  # 데이터 총 수량을 획득

        for i in range(data_cnt):  # 반복문으로 데이터를 하나씩 가져옴
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    # 주식 분봉차트 조회 요청의 답변처리
    def _opt10080(self, rqname, trcode):  # opt10080에 대한 답변을 함수로 호출
        # data_cnt = 390 #self._get_repeat_cnt(trcode, rqname) #데이터 총 수량을 획득
        data_cnt = 60  # self._get_repeat_cnt(trcode, rqname) #데이터 총 수량을 획득, 장중 조회시는 3개로 제한
        for i in range(data_cnt):  # 반복문으로 데이터를 하나씩 가져옴
            time = self._comm_get_data(trcode, "", rqname, i, "체결시간")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            # print(time, open, high, low, close, volume)

            self.ohlcv['time'].append(time)
            self.ohlcv['open'].append(abs(int(open)))
            self.ohlcv['high'].append(abs(int(high)))
            self.ohlcv['low'].append(abs(int(low)))
            self.ohlcv['close'].append(abs(int(close)))
            self.ohlcv['volume'].append(int(volume))

    # 계좌정보를 리셋
    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    # 계좌 총 정보
    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))

        total_earning_rate = Kiwoom.change_format(total_earning_rate)

        # 모의투자와 실투자 간의 수익률 표현이 달라, 모의투자일 경우 아래 처리가 추가됨
        if self.get_server_gubun():
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(total_earning_rate)
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            num = self._comm_get_data(trcode, "", rqname, i, "종목번호")
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            strip_num = num.lstrip('A')  # 종목번호 왼쪽의 A를 없앰
            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append(
                [strip_num, name, quantity, purchase_price, current_price, eval_profit_loss_price,
                 earning_rate])

    def reset_opt10087_output(self):
        self.opt10087_output = {'single': [], 'multi': []}

    # 시간외단일가 요청의 답변 처리
    def _opt10087(self, rqname, trcode):  # opt10087에 대한 답변을 함수로 호출
        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            self.ck_time = self._comm_get_data(trcode, "", rqname, 0, "호가잔량기준시간")
            ck_price = self._comm_get_data(trcode, "", rqname, 0, "시간외단일가_매도호가1")
            ck_price = ck_price.lstrip('+-')  # 앞의 부호 제거
            self.opt10087_output['multi'].append([ck_price])

    def reset_opt10004_output(self):
        self.opt10004_output = {'single': [], 'multi': []}

    # 주식호가요청 요청의 답변 처리
    def _opt10004(self, rqname, trcode):  # opt10004에 대한 답변을 함수로 호출
        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            self.hoga_time = self._comm_get_data(trcode, "", rqname, 0, "호가잔량기준시간")
            sell_janrang_total = int(self._comm_get_data(trcode, "", rqname, 0, "총매도잔량"))
            sell_janrang_7hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매도7차선잔량"))
            sell_janrang_6hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매도6우선잔량"))
            sell_janrang_5hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매도5차선잔량"))
            sell_janrang_4hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매도4차선잔량"))
            sell_janrang_3hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매도3차선잔량"))
            sell_janrang_2hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매도2차선잔량"))
            sell_janrang_1hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매도최우선잔량"))
            hoga_buy_price = self._comm_get_data(trcode, "", rqname, 0, "매도최우선호가")
            hoga_sell_price = self._comm_get_data(trcode, "", rqname, 0, "매수최우선호가")
            buy_janrang_1hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매수최우선잔량"))
            buy_janrang_2hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매수2차선잔량"))
            buy_janrang_3hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매수3차선잔량"))
            buy_janrang_4hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매수4차선잔량"))
            buy_janrang_5hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매수5차선잔량"))
            buy_janrang_6hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매수6우선잔량"))
            buy_janrang_7hoga = int(self._comm_get_data(trcode, "", rqname, 0, "매수7차선잔량"))
            buy_janrang_total = int(self._comm_get_data(trcode, "", rqname, 0, "총매수잔량"))

            hoga_sell_price = int(hoga_sell_price.lstrip('+-'))  # 앞의 부호 제거
            hoga_buy_price = int(hoga_buy_price.lstrip('+-'))  # 앞의 부호 제거
            sell_janrang_3hap = sell_janrang_1hoga + sell_janrang_2hoga + sell_janrang_3hoga
            sell_janrang_5hap = sell_janrang_3hap + sell_janrang_4hoga + sell_janrang_5hoga
            sell_janrang_7hap = sell_janrang_5hap + sell_janrang_6hoga + sell_janrang_7hoga
            buy_janrang_3hap = buy_janrang_1hoga + buy_janrang_2hoga + buy_janrang_3hoga
            buy_janrang_5hap = buy_janrang_3hap + buy_janrang_4hoga + buy_janrang_5hoga
            buy_janrang_7hap = buy_janrang_5hap + buy_janrang_6hoga + buy_janrang_7hoga
            diff_total = buy_janrang_total - sell_janrang_total
            diff_7hap = buy_janrang_7hap - sell_janrang_7hap
            diff_5hap = buy_janrang_5hap - sell_janrang_5hap
            diff_3hap = buy_janrang_3hap - sell_janrang_3hap
            diff_1hap = buy_janrang_1hoga - sell_janrang_1hoga

            self.opt10004_output['multi'].append([hoga_sell_price, hoga_buy_price, sell_janrang_7hap, sell_janrang_5hap, sell_janrang_3hap, sell_janrang_1hoga, buy_janrang_1hoga, buy_janrang_3hap, buy_janrang_5hap, buy_janrang_7hap, diff_7hap, diff_5hap, diff_3hap, diff_1hap])
    # 주식체결요청 요청의 답변 처리
    def _opt10012(self, rqname, trcode):  # opt10001에 대한 답변을 함수로 호출
        # single data
        print('opt10012')
        self.chejan_num = self._comm_get_data(trcode, "", rqname, 0, "주문수량")
        self.chejan_price = self._comm_get_data(trcode, "", rqname, 0, "주문가격")
        self.chejan_id = self._comm_get_data(trcode, "", rqname, 0, "원주문번호")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()  # Kiwoom 클래스로 인스턴스 생성
    kiwoom.comm_connect()  # 키움 연결창 발생

    # 실시간 조회 테스트
    # kiwoom.set_input_value("종목코드", "233740")
    # kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "0101")
    # print(kiwoom.current_price)
    # kiwoom.dynamicCall("GetCommRealData(122630, 10)")
    # kiwoom.get_comm_real_data("122630", 10)

    # kiwoom.reset_opw00018_output()
    # account_number = kiwoom.get_login_info("ACCNO")
    # account_number = account_number.split(';')[0]

    # kiwoom.set_input_value("계좌번호", account_number)
    # kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")
    # print(kiwoom.opw00018_output['single'])
    # print(kiwoom.opw00018_output['multi'])

    # opt10081 TR 요청 - 주식일봉차트
    # kiwoom.set_input_value("종목코드", "039490")
    # kiwoom.set_input_value("기준일자", "20170224")
    # kiwoom.set_input_value("수정주가구분", 1)
    # kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

    # while kiwoom.remained_data == True:
    #    time.sleep(TR_REQ_TIME_INTERVAL)
    #    kiwoom.set_input_value("종목코드", "039490")
    #    kiwoom.set_input_value("기준일자", "20170224")
    #    kiwoom.set_input_value("수정주가구분", 1)
    #    kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

    # opt10080 TR 요청 - 주식분봉차트
    # kiwoom.set_input_value("종목코드", "122630")
    # kiwoom.set_input_value("틱범위", "1")
    # kiwoom.set_input_value("수정주가구분", 1)
    # kiwoom.comm_rq_data("opt10080_req", "opt10080", 0, "0101")

    # while kiwoom.remained_data == True:
    #    time.sleep(TR_REQ_TIME_INTERVAL)
    #    kiwoom.set_input_value("종목코드", "039490")
    #    kiwoom.set_input_value("틱범위", "1")
    #    kiwoom.set_input_value("수정주가구분", 1)
    #    kiwoom.comm_rq_data("opt10080_req", "opt10080", 2, "0101")

    # opt10004 TR 요청 - 주식호가요청
    kiwoom.reset_opt10004_output()
    kiwoom.set_input_value("종목코드", "233740")
    kiwoom.comm_rq_data("opt10004_req", "opt10004", 0 ,"0101")
