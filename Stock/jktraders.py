import sys
from PyQt5.QtWidgets import *
# from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from Kiwoom_API import *
from datetime import datetime, timedelta
import FinanceDataReader as fdr
# import datetime
# import time
# import os
# from pandas import DataFrame
# import re
# import numpy as np
# import pandas as pd

MARKET_KOSPI   = 0
MARKET_KOSDAQ  = 10

# UI 호출
form_class = uic.loadUiType("jktraders.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # 전일 주요 지수 정보 확인
        daw_predayinfo = self.get_predayinfo('DJI')     # 다우지수 전일 정보 확인
        nasdaq_predayinfo = self.get_predayinfo('IXIC') # 나스닥지수 전일 정보 확인
        us500_predayinfo = self.get_predayinfo('US500') # S&P500지수
        kospi_predayinfo = self.get_predayinfo('KS11')  # KOSPI지수
        kosdaq_predayinfo = self.get_predayinfo('KQ11') # KOSDAQ지수

        # 키움 로그인 진행
        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

        def get_openprice(self, code):
            self.kiwoom.set_input_value("종목코드", code)
            self.kiwoom.comm_rq_data("opt10001_req", "opt10001", 0, "1001")
            return

        self.S1_233740_buy = 0          # 매수대상인지 확인용 변수
        self.S1_233740_amount = 1       # 매수수량
        self.S1_233740_openprice = 0    # 시작가
        self.S1_233740_down = 0         # 하락기록 누적 횟수
        self.S1_233740_sell1 = 0        # 매도 체크1
        self.S1_233740_sell2 = 0        # 매도 체크2
        self.S1_233740_sell3 = 0        # 매도 체크3
        self.S1_233740_pre_5hap = 0     # 이전 5호가합 저장용

        self.S1_251340_buy = 0          # 매수대상인지 확인용 변수
        self.S1_251340_amount = 1       # 매수수량
        self.S1_251340_openprice = 0    # 시작가
        self.S1_251340_down = 0         # 하락기록 누적 횟수
        self.S1_251340_sell1 = 0        # 매도 체크1
        self.S1_251340_sell2 = 0        # 매도 체크2
        self.S1_251340_sell3 = 0        # 매도 체크3
        self.S1_251340_pre_5hap = 0     # 이전 5호가합 저장용

        # S1-장시작 전 호가잔량을 보고 매수, 3연속 잔량 하락시 반매도, 3,5,총합이 음수면 반매도
        # 10초 단위 판단 : 9시 이후, 3,5,총이 모두 음수 기록시 절반 매도
        # 매수 이후부터 3연속 5차이가 하락하면 절반 매도

        # 1초마다 반복하는 이벤트 발생
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        # 10초마다 반복하는 이벤트 발생
        self.timer2 = QTimer(self)
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)

        # 종목이름 입력 시 번호 전환 표기
        self.ui_stockcode_LE.textChanged.connect(self.code_changed)

        # 사용자 정보 획득 - 언제 필요한 정보인지 검토 필요
        id = self.kiwoom.dynamicCall('GetLoginInfo("USER_ID")')
        name = self.kiwoom.dynamicCall('GetLoginInfo("USER_NAME")')
        accounts_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accounts_num]
        self.ui_accountlist_CB.addItems(accounts_list)
        self.ui_sendorder_PB.clicked.connect(self.send_order)
        self.ui_check_PB.clicked.connect(self.check_balance)
        self.account1 = accounts_list[0]

    # 미국, 한국 증시 전일정보 확인
    def get_predayinfo(self, CODE):
        day = datetime.today() - timedelta(10)
        df = fdr.DataReader(CODE, day)
        rows = len(df)
        today_close = df.iloc[rows -1]['Close']     # 직전 종가
        today_open = df.iloc[rows -1]['Open']       # 직전 시가
        yesterday = df.iloc[rows -2]['Close']       # 전일 종가
        lastday = df.index[rows - 1]                # 최종거래일

        # 판단 참고 지표
        diff = today_close - yesterday              # 전일 대비 증감
        rate = (diff / yesterday) * 100             # 증감비율
        bong = today_close - today_open             # 당일 봉차트

        # 출력할 결과값 정리 (종가, 전일대비증감값, 전일대비증감비, 당일 변경 봉값)
        result = [round(today_close, 2), round(diff, 2), round(rate, 2), round(bong, 2)]

        # 전일 대비 종가를 화살표로 표기
        if diff > 0:    diff_graph = '▲'
        elif diff < 0:  diff_graph = '▼'
        else:           diff_graph = '-'

        # 당일 종가를 화살표로 표기
        if bong >= 0:   bong_graph = '↗'
        else:           bong_graph = '↘'

        # 각 코드 별 UI 반영
        if CODE == 'DJI':
            ui_result = str(result[0]) + bong_graph + '(' + str(result[2]) + '/' + str(result[3]) + '%' + diff_graph + ')'
            if diff_graph == '▼':    self.ui_daw30_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
            else:                   self.ui_daw30_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
            self.ui_daw30_LE.setText(ui_result)
            self.ui_uslastday_LE.setText(str(lastday)[:10])
            print(CODE, result)
        elif CODE == 'IXIC':
            ui_result = str(result[0]) + bong_graph + '(' + str(result[2]) + '/' + str(result[3]) + '%' + diff_graph + ')'
            if diff_graph == '▼':    self.ui_nasdaq_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
            else:                   self.ui_nasdaq_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
            self.ui_nasdaq_LE.setText(ui_result)
            print(CODE, result)
        elif CODE == 'US500':
            ui_result = str(result[0]) + bong_graph + '(' + str(result[2]) + '/' + str(result[3]) + '%' + diff_graph + ')'
            if diff_graph == '▼':    self.ui_us500_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
            else:                   self.ui_us500_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
            self.ui_us500_LE.setText(ui_result)
            print(CODE, result)
        elif CODE == 'KS11':
            ui_result = str(result[0]) + bong_graph + '(' + str(result[2]) + '/' + str(result[3]) + '%' + diff_graph + ')'
            if diff_graph == '▼':    self.ui_kospi_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
            else:                   self.ui_kospi_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
            self.ui_kospi_LE.setText(ui_result)
            self.ui_kolastday_LE.setText(str(lastday)[:10])
            print(CODE, result)
        elif CODE == 'KQ11':
            ui_result = str(result[0]) + bong_graph + '(' + str(result[2]) + '/' + str(result[3]) + '%' + diff_graph + ')'
            if diff_graph == '▼':    self.ui_kosdaq_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
            else:                   self.ui_kosdaq_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
            self.ui_kosdaq_LE.setText(ui_result)
            print(CODE, result)
        return result

    ### 종목 정의
    stocks_code = []        # 종목별 코드
    stocks_name = []        # 종목별 종목명
    stocks_preprice = []    # 종목별 전일가
    stocks_openprice = []   # 종목별 시작가
    stocks_price = []       # 종목별 현재가

    # stocks.txt 파일에서 종목명 확인하여 리스트로 저장
    f = open("stocks.txt", 'r')
    while True:
        line = f.readline().strip() # 줄 끝의 줄 바꿈 문자를 제거한다.
        if not line: break
        stocks_name.append(line)

    # 종목코드 확인
    for stock in (stocks_name):
        print(stock)

    # 1초마다 반복하는 이벤트
    def timeout(self):
        current_time = QTime.currentTime()
        self.text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + self.text_time

        # 연결 상태를 확인하여 상태표시줄에 표기
        state = self.kiwoom.GetConnectState()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"
        self.statusbar.showMessage(state_msg + " | " + time_msg)

    # 10초마다 반복하는 이벤트
    def timeout2(self):
        current_time = QTime.currentTime()

        if self.ui_realtime_CB.isChecked():
            self.check_balance()

        if current_time > QTime(8, 57, 0) and current_time < QTime(15, 31, 0):
            # 기본정보조회
            self.kiwoom.reset_opt10004_output()
            self.kiwoom.set_input_value("종목코드", '233740')
            self.kiwoom.comm_rq_data("opt10004_req", "opt10004", 0, "0101")

            imsi = self.kiwoom.opt10004_output['multi'][0]
            data_233740 = [self.text_time, imsi[0], imsi[1], imsi[2], imsi[3], imsi[4], imsi[5], imsi[6], imsi[7], imsi[8],
                           imsi[9], imsi[10], imsi[11], imsi[12], imsi[13]]
            print(data_233740)

            f = open('newfile_233740.txt', 'a')
            f.write(str(data_233740))
            f.write("\n")
            f.close()

            # 기본정보조회
            self.kiwoom.reset_opt10004_output()
            self.kiwoom.set_input_value("종목코드", '251340')
            self.kiwoom.comm_rq_data("opt10004_req", "opt10004", 0, "0101")

            imsi = self.kiwoom.opt10004_output['multi'][0]
            data_251340 = [self.text_time, imsi[0], imsi[1], imsi[2], imsi[3], imsi[4], imsi[5], imsi[6], imsi[7], imsi[8],
                           imsi[9], imsi[10], imsi[11], imsi[12], imsi[13]]
            print(data_251340)

            f = open('newfile_251340.txt', 'a')
            f.write(str(data_251340))
            f.write("\n")
            f.close()

        # 장 전 매수여부 판단용
        if current_time >= QTime(8, 59, 50) and current_time < QTime(9, 0, 0):
            # 직전 3합차, 5합차이 둘다 양수면 매수 중 하나라도 마이너스면 매수 대상에서 제외
            if data_233740[12] > 0 and data_233740[13] > 0:
                self.S1_233740_buy = 1
                print('레버리지 매수')
                self.ui_history_TE.append(self.text_time + " 233740 매수 : " + str(data_233740[2]))

                lRet = self.kiwoom.send_order("send_order_req", "0101", self.account1, 1, 233740, (self.S1_233740_amount), 0, "03", "")
                if lRet == 0:
                    print("주문성공")
                else:
                    print("주문실패")

            if data_251340[12] > 0 or data_251340[13] > 0:
                self.S1_251340_buy = 1
                print('인버스 매수')

                lRet = self.kiwoom.send_order("send_order_req", "0101", self.account1, 1, 251340, (self.S1_251340_amount), 0, "03", "")
                if lRet == 0:
                    print("주문성공")
                else:
                    print("주문실패")

        # 매도 시점 판단용
        if current_time > QTime(9, 0, 0):

            # 레버리지
            if self.S1_233740_buy == 1:
                # 5합이 연속 하락인 지 계산
                if data_233740[12] < self.S1_233740_pre_5hap:
                    self.S1_233740_down = self.S1_233740_down + 1
                else:
                    self.S1_233740_down = 0
                
                # 조건 3: 5차가 3번연속 줄어들고, 5,3차가 모두 -찍을때 매도
                if self.S1_233740_down == 3 and data_233740[12] < 0 and data_233740[13] and self.S1_233740_sell3 == 0:
                    self.S1_233740_sell3 = 1
                    print('레버리지 매도 - 호가5호합이 3연속 줄어들고, 5,3차가 마이너스')
                    self.ui_history_TE.append(self.text_time + " 233740 매도3 : " + str(data_233740[1]))

                    lRet = self.kiwoom.send_order("send_order_req", "0101", self.account1, 2, 233740, self.S1_233740_amount, 0, "03", "")
                    if lRet == 0:
                        print("주문성공")
                    else:
                        print("주문실패")

            self.S1_233740_pre_5hap = data_233740[12]

            # Inverse
            # 매수가 유효한가?
            if self.S1_251340_buy == 1:
                # 5합이 연속 하락인 지 계산
                if data_251340[12] < self.S1_251340_pre_5hap:
                    self.S1_251340_down = self.S1_251340_down + 1
                else:
                    self.S1_251340_down = 0

                # 조건 3: 5차가 3번연속 줄어들고, 5,3차가 모두 -찍을때 매도 2
                if self.S1_251340_down == 3 and data_251340[12] < 0 and data_251340[13] and self.S1_251340_sell3 == 0:
                    self.S1_251340_sell3 = 1
                    print('Inverse 매도 - 호가5호합이 3연속 줄어들고, 5,3차가 마이너스')
                    self.ui_history_TE.append(self.text_time + " 251340 매도3 : " + str(data_251340[1]))

                    lRet = self.kiwoom.send_order("send_order_req", "0101", self.account1, 2, 251340, self.S1_251340_amount, 0, "03", "")
                    if lRet == 0:
                        print("주문성공")
                    else:
                        print("주문실패")

            self.S1_251340_pre_5hap = data_251340[12]


    # 코드를 받아서 종목명으로 출력
    def code_changed(self):
        code = self.ui_stockcode_LE.text()
        name = self.kiwoom.get_master_code_name(code)
        self.ui_stockname_LE.setText(name)

    # 매수 주문 (수동 주문)
    def send_order(self):
        order_type_lookup = {'신규매수':1, '신규매도':2, '매수취소':3, '매도취소':4}
        hoga_lookup = {'지정가':"00", '시장가':"03"}

        account = self.ui_accountlist_CB.currentText()
        order_type = self.ui_ordertype_CB.currentText()
        code = self.ui_stockcode_LE.text()
        hoga = self.ui_hoga_CB.currentText()
        num = self.ui_num_SB.value()
        price = self.ui_price_SB.value()

        if code == '' or self.ui_stockname_LE.text() == '':
            print(self.text_time + ' code is empty')
            self.ui_history_TE.append(self.text_time + " 코드가 입력되지 않았습니다")
        elif num < 1 or price < 1:
            print(self.text_time + ' num or price is 0')
            self.ui_history_TE.append(self.text_time + " 수량이나 가격이 정상입력되지 않았습니다")
        else:
            ret = self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, num, price, hoga_lookup[hoga], "")
            if ret == 0:
                self.ui_history_TE.append(self.text_time + " 주문이 전송 되었습니다")
                self.ui_history_TE.append(self.text_time + " " + code+'/'+str(num)+'/'+str(price)+'/'+order_type+'/'+hoga)
            else:
                self.ui_history_TE.append(self.text_time + " 주문이 전송 실패 하였습니다")
                self.ui_history_TE.append(self.text_time + ' ' + code+'/'+str(num)+'/'+str(price)+'/'+order_type+'/'+hoga)

    # 매수 주문 (자동)
    def send_order2(self, rqname, screen_no, order_type_lookup, code, num, price, hoga, order_no):
        lRet = self.kiwoom.send_order("send_order_req", "0101", self.account1, 1, code, num, price, "03", "")
        if lRet == 0:
            print("주문성공")
        else:
            print("주문실패")
        return lRet

    # 계좌 잔고 정보
    def check_balance(self):
        self.kiwoom.reset_opw00018_output()  # 저장할 배열을 초기화
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        # 계좌 잔고
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data:
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # 예수금 정보
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.ui_balance_TW.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.ui_balance_TW.setItem(0, i, item)

        self.ui_balance_TW.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.ui_stockstatus_TW.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.ui_stockstatus_TW.setItem(j, i, item)

        self.ui_stockstatus_TW.resizeRowsToContents()

    # TR Data 처리 함수
    def _ReceiveTrData(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        # print('RQ:', rqname)
        if rqname == "주식기본정보":
            nCnt = int(self.kiwoom.dynamicCall('GetRepeatCnt(QString, QString)', trcode, rqname)) +1
            for nIdx in range(0, nCnt):
                code = self._get_comm_data(trcode, rqname, nIdx, "종목코드")
                name = self._get_comm_data(trcode, rqname, nIdx, "종목명")
                volume = self._get_comm_data(trcode, rqname, nIdx, "거래량")
                open = self._get_comm_data(trcode, rqname, nIdx, "시가")
                high = self._get_comm_data(trcode, rqname, nIdx, "고가")
                low = self._get_comm_data(trcode, rqname, nIdx, "저가")
                close = self._get_comm_data(trcode, rqname, nIdx, "현재가")
                rate = self._get_comm_data(trcode, rqname, nIdx, "등락율")

                # self.openprice = self.change_format(open)
                self.close = self.change_format(close)

                print(code, name, close, rate)
            return

        elif rqname == "시가정보":
            self.openprice = self.change_format(self._get_comm_data(trcode, rqname, 0, "시가"))
            if self.openprice > 0:
                self.ui_history_TE.append("시작가: " + str(self.openprice))

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            print('except')
            pass



'''
        # 변수 선언
        self.common_variable()
        
        self.startButton.clicked.connect(lambda: self.buttonClicked('start'))
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveTrData.connect(self._ReceiveTrData)
        self.kiwoom.OnReceiveRealData.connect(self._ReceiveRealData)
        self.kiwoom.OnReceiveChejanData.connect(self._ReceiveChejanData)

    # 체결 정보 표기 - 매수/매도 주문 및 체결 시 작동
    def _ReceiveChejanData(self, gubun, item_cnt, fid_list):
        if gubun == "0":
            self.v233740_ordernum = self.kiwoom.get_chejan_data(9203)
            print('ordernum', self.v233740_ordernum)
            self.ui_history_TE.append("구분: 주문체결통보")
            self.ui_history_TE.append("주문/체결시간: " +  self.kiwoom.get_chejan_data(908))
            self.ui_history_TE.append("종목명: " + self.kiwoom.get_chejan_data(302))
            self.ui_history_TE.append("주문수량: " + self.kiwoom.get_chejan_data(900))
            self.ui_history_TE.append("체결수량: " + self.kiwoom.get_chejan_data(911))
            self.ui_history_TE.append("체결가격: " + self.kiwoom.get_chejan_data(910))
            self.ui_history_TE.append("주문번호: " + self.kiwoom.get_chejan_data(9203))
            self.ui_history_TE.append("============================")
        elif gubun == "1":
            self.ui_history_TE.append("구분: 잔고통보")
            # self.ui_history_TE.append("주문/체결시간: " + self.kiwoom.get_chejan_data(908))
            self.ui_history_TE.append("종목명: " + self.kiwoom.get_chejan_data(302))
            # self.ui_history_TE.append("체결수량: " + self.kiwoom.get_chejan_data(911))
            self.ui_history_TE.append("종목코드: " + self.kiwoom.get_chejan_data(9001))
            self.ui_history_TE.append("보유수량: " + self.kiwoom.get_chejan_data(930))
            self.ui_history_TE.append("예수금: " + self.kiwoom.get_chejan_data(951))
            self.ui_history_TE.append("============================")
            buysell = self.kiwoom.get_chejan_data(946)
            #order_num = self.get_chejan_data(9203)
            self.v233740_amount = self.kiwoom.get_chejan_data(930)
            print('잔고통보', gubun, self.v233740_amount, buysell)

        elif gubun == "3":
            self.ui_history_TE.append("구분: 특이신호")

    # 실시간 데이터 처리
    def _ReceiveRealData(self, code, type1, data):
        if type1 == "주식체결":
            self.realclose = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 10)"))
            volume = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 15)"))
            self.sellhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 27)"))
            self.buyhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 28)"))
            self.chegang = float(self.kiwoom.dynamicCall("GetCommRealData(QString, 228)"))
            self.text_time = self.cur_time.toString("hh:mm:ss")

            if self.chegang < 500:
                self.real_count = self.real_count + 1
                chegangflowcount = self.real_count % 5
                self.chegangflow[chegangflowcount] = self.chegang


        if type1 == "주식우선호가":
            self.presellhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 27)"))
            self.prebuyhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 28)"))
            self.text_time = self.cur_time.toString("hh:mm:ss")

            # 장전 10분동안 주식 매수호가 연속성 확인
            if self.cur_time >= QTime(8, 50, 0) and self.cur_time < QTime(9, 0, 0):
                print("장전매수호가:", self.prebuyhoga, self.text_time)

        return

    def get_predata(self, code):
        df = self.get_ohlcv(code, 1)

        preprice = df.iloc[1]['close']
        prevolume = df.iloc[1]['volume']
        prepreprice = df.iloc[2]['close']
        return preprice, prevolume, prepreprice

    # ====================== 키움 Open API =======================

    # 시가정보
    def get_openprice(self, code):
        self.set_input_value("종목코드", code)
        self.comm_rq_data("시가정보", "opt10001", 0, "1001")
        return
    
    def get_info(self, df_code_s, code, count, thick):
        now = datetime.datetime.now()  # 함수 수행 시간
        time = now.strftime('%H%M%S')

        chegangdata = self.get_chegang(code)
        volume = chegangdata['volume']
        chegang = self.chegangdata['chegang']

        df_code_s.loc[count] = [time, count, volume, chegang]

        return 1
    
    def get_chegang(self, code):
        self.chegang = {'code':[], 'date':[], 'volume':[], 'chegang':[]}
        self.chegang['code'] = code
        self.set_input_value("종목코드", code)
        self.comm_rq_data("체결정보조회", "opt10005", 0, "0001")

        return self.chegang

    def show_info(self, df, code, count, interval):
        time = df.ix[count]['time']
        volume = df.ix[count]['volume']
        chegang = df.ix[count]['chegang']

        print(interval, ":", time, "%4d" % df.ix[count]['count'], volume, chegang)


# ================================================================================ 키움클래스

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        # self._set_signal_slots()

    # COM을 사용하기 위한 메서드
    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    # 로그인 메서드, 로그인 과정에서 프로그램이 진행되면 안되기 때문에 이벤트 루프 생성
    def comm_connect(self):
        v = self.dynamicCall("CommConnect()")
        #self.login_event_loop = QEventLoop()
        #self.login_event_loop.exec_()
        return v


    def get_code_list(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret
        '''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
