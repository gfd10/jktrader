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

        # 키움 로그인 진행
        self.kiwoom = Kiwoom()
        # self.kiwoom.comm_connect()

        # 전일 정보 확인
        self.get_info()

        # 다우지수 전일 정보 확인
        DJI_predayinfo = self.get_predayinfo('DJI')
        print(DJI_predayinfo)

        # 나스닥지수 전일 정보 확인
        IXIC_predayinfo = self.get_predayinfo('IXIC')
        print(IXIC_predayinfo)

        # S&P500지수
        US500_predayinfo = self.get_predayinfo('US500')
        print(US500_predayinfo)

        # 1초마다 반복하는 이벤트 발생
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)
        '''
        # 10초마다 반복하는 이벤트 발생
        self.timer2 = QTimer(self)
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)

        # 종목이름 입력 시 번호 전환 표기
        self.ui_stockcode_LE.textChanged.connect(self.code_changed)

        # 사용자 정보 획득
        # id = self.kiwoom.dynamicCall('GetLoginInfo("USER_ID")')
        # name = self.kiwoom.dynamicCall('GetLoginInfo("USER_NAME")')
        accounts_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT"))
        accounts = self.kiwoom.get_login_info("ACCNO")
        accounts_list = accounts.split(';')[0:accounts_num]
        self.ui_accountlist_CB.addItems(accounts_list)
        self.ui_sendorder_PB.clicked.connect(self.send_order)
        self.ui_check_PB.clicked.connect(self.check_balance)
        # self.account1 = accounts_list[0]
        '''
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
        result = [today_close, diff, rate, bong]
        return result

    def get_info(self):
        day = datetime.today() - timedelta(10)

        df_kospi = fdr.DataReader('KS11', day)
        df_kosdaq = fdr.DataReader('KQ11', day)
        # df_china = fdr.DataReader('CSI300', day)

        ### 다우지수
        df_DJI = fdr.DataReader('DJI', day)
        rows = len(df_DJI)
        today_close = df_DJI.iloc[rows - 1]['Close']    # 직전 종가
        today_open = df_DJI.iloc[rows - 1]['Open']      # 직전 시가
        yesterday = df_DJI.iloc[rows - 2]['Close']      # 전일 종가
        lastday = df_DJI.index[rows - 1]
        # 판단 참고 지표
        daw_diff = today_close - yesterday                  # 전일 대비 증감
        daw_rate = ((today_close - yesterday) / yesterday) * 100    # 증감비율
        daw_bong = today_close - today_open                 # 당일 봉차트
        # 전일 대비 종가를 화살표로 표기
        if daw_diff > 0:
            diff_graph = '%▲'
            self.ui_daw30_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
        elif daw_diff < 0:
            diff_graph = '%▼'
            self.ui_daw30_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
        else:
            diff_graph = '-'
        # 당일 종가를 화살표로 표기
        if daw_bong >= 0:
            bong_graph = '↗'
        else:
            bong_graph = '↘'
        # 출력할 결과값 정리
        daw30_result = str(round(today_close, 2)) + bong_graph + '(' + str(round(daw_diff, 2)) + '/' + str(round(daw_rate, 2)) + diff_graph + ')'
        # UI에 표기
        self.ui_daw30_LE.setText(daw30_result)

        self.ui_uslastday_LE.setText(str(lastday)[:10])

        ### 나스닥지수
        df_IXIC = fdr.DataReader('IXIC', day)
        rows = len(df_IXIC)
        today_close = df_IXIC.iloc[rows - 1]['Close']  # 직전 종가
        today_open = df_IXIC.iloc[rows - 1]['Open']  # 직전 시가
        yesterday = df_IXIC.iloc[rows - 2]['Close']  # 전일 종가
        # 판단 참고 지표
        ixic_diff = today_close - yesterday  # 전일 대비 증감
        ixic_rate = ((today_close - yesterday) / yesterday) * 100  # 증감비율
        ixic_bong = today_close - today_open  # 당일 봉차트
        # 전일 대비 종가를 화살표로 표기
        if ixic_diff > 0:
            diff_graph = '%▲'
            self.ui_nasdaq_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
        elif ixic_diff < 0:
            diff_graph = '%▼'
            self.ui_nasdaq_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
        else:
            diff_graph = '-'
        # 당일 종가를 화살표로 표기
        if ixic_bong >= 0:
            bong_graph = '↗'
        else:
            bong_graph = '↘'
        # 출력할 결과값 정리
        ixic_result = str(round(today_close, 2)) + bong_graph + '(' + str(round(ixic_diff, 2)) + '/' + str(
            round(ixic_rate, 2)) + diff_graph + ')'
        # UI에 표기
        self.ui_nasdaq_LE.setText(ixic_result)

        ### S&P500지수
        df_US500 = fdr.DataReader('US500', day)
        rows = len(df_US500)
        today_close = df_US500.iloc[rows - 1]['Close']  # 직전 종가
        today_open = df_US500.iloc[rows - 1]['Open']  # 직전 시가
        yesterday = df_US500.iloc[rows - 2]['Close']  # 전일 종가
        # 판단 참고 지표
        us500_diff = today_close - yesterday  # 전일 대비 증감
        us500_rate = ((today_close - yesterday) / yesterday) * 100  # 증감비율
        us500_bong = today_close - today_open  # 당일 봉차트
        # 전일 대비 종가를 화살표로 표기
        if us500_diff > 0:
            diff_graph = '%▲'
            self.ui_us500_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
        elif us500_diff < 0:
            diff_graph = '%▼'
            self.ui_us500_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
        else:
            diff_graph = '-'
        # 당일 종가를 화살표로 표기
        if us500_bong >= 0:
            bong_graph = '↗'
        else:
            bong_graph = '↘'
        # 출력할 결과값 정리
        us500_result = str(round(today_close, 2)) + bong_graph + '(' + str(round(us500_diff, 2)) + '/' + str(
            round(us500_rate, 2)) + diff_graph + ')'
        # UI에 표기
        self.ui_us500_LE.setText(us500_result)

        ### 코스피
        df_kospi = fdr.DataReader('KS11', day)
        rows = len(df_kospi)
        today_close = df_kospi.iloc[rows - 1]['Close']  # 직전 종가
        today_open = df_kospi.iloc[rows - 1]['Open']  # 직전 시가
        yesterday = df_kospi.iloc[rows - 2]['Close']  # 전일 종가
        lastday = df_kospi.index[rows - 1]
        # 판단 참고 지표
        kospi_diff = today_close - yesterday  # 전일 대비 증감
        kospi_rate = ((today_close - yesterday) / yesterday) * 100  # 증감비율
        kospi_bong = today_close - today_open  # 당일 봉차트
        # 전일 대비 종가를 화살표로 표기
        if kospi_diff > 0:
            diff_graph = '%▲'
            self.ui_kospi_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
        elif kospi_diff < 0:
            diff_graph = '%▼'
            self.ui_kospi_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
        else:
            diff_graph = '-'
        # 당일 종가를 화살표로 표기
        if kospi_bong >= 0:
            bong_graph = '↗'
        else:
            bong_graph = '↘'
        # 출력할 결과값 정리
        kospi_result = str(round(today_close, 2)) + bong_graph + '(' + str(round(kospi_diff, 2)) + '/' + str(
            round(kospi_rate, 2)) + diff_graph + ')'
        # UI에 표기
        self.ui_kospi_LE.setText(kospi_result)

        self.ui_kolastday_LE.setText(str(lastday)[:10])

        ### 코스닥
        df_kosdaq = fdr.DataReader('KQ11', day)
        rows = len(df_kosdaq)
        today_close = df_kosdaq.iloc[rows - 1]['Close']  # 직전 종가
        today_open = df_kosdaq.iloc[rows - 1]['Open']  # 직전 시가
        yesterday = df_kosdaq.iloc[rows - 2]['Close']  # 전일 종가
        # 판단 참고 지표
        kosdaq_diff = today_close - yesterday  # 전일 대비 증감
        kosdaq_rate = ((today_close - yesterday) / yesterday) * 100  # 증감비율
        kosdaq_bong = today_close - today_open  # 당일 봉차트
        # 전일 대비 종가를 화살표로 표기
        if kosdaq_diff > 0:
            diff_graph = '%▲'
            self.ui_kosdaq_LE.setStyleSheet("color : red;""background-color : rgb(240, 240, 240);")
        elif kosdaq_diff < 0:
            diff_graph = '%▼'
            self.ui_kosdaq_LE.setStyleSheet("color : blue;""background-color : rgb(240, 240, 240);")
        else:
            diff_graph = '-'
        # 당일 종가를 화살표로 표기
        if kosdaq_bong >= 0:
            bong_graph = '↗'
        else:
            bong_graph = '↘'
        # 출력할 결과값 정리
        kosdaq_result = str(round(today_close, 2)) + bong_graph + '(' + str(round(kosdaq_diff, 2)) + '/' + str(
            round(kosdaq_rate, 2)) + diff_graph + ')'
        # UI에 표기
        self.ui_kosdaq_LE.setText(kosdaq_result)

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

    print(stocks_name)
    print(type(stocks_name))
    # 1. 전일가 확인

    # 2. 시작가 확인
    # 3. 1초마다 현재가 확인 (최고가, 최저가 갱신)
    # +예상가 확인
    # +예상가 도달여부 확인


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
        if self.ui_realtime_CB.isChecked():
            self.check_balance()

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

'''
        if self.starttrading == True:

            

            # 장전매수주문
            if self.cur_time >= QTime(8, 58, 0) and self.position != 'holding' and self.sb_buy == False:
                self.sb_buy = True
                print(self.text_time, '장전매수주문', self.prebuyhoga, self.sb_num)
                self.ui_sb.append('장전매수주문')
                if self.ui_sb_realtrade.isChecked() == True:
                    self.send_order("send_order_rq", "0101", self.account1, 1, str(self.code), self.sb_num, 0, "03", "")

                # print(self.text_time, "장전매수여부확인", self.prebuyhoga)
                # if self.prebuyhoga >= self.preprice * 0.97:
                    # self.sb_num = int((self.deposit * 0.8)/self.prebuyhoga)

            # 시작가 받아오기
            if self.cur_time >= QTime(9, 0, 0) and self.openprice == 0 and self.login == True:
                self.get_openprice(str(self.code))

            # 잔고 남았을때 시가매매 손절 조건
            if self.sb_num > 0:
                # 9시 5분까지 잔량확인 후 손절체크 on
                if self.cur_time >= QTime(9, 5, 0) and self.sb_check05 == 0:
                    self.sb_check05 = 1
                    self.sb_sell = True # 손절 on
                    print("5분 현재가", self.realclose)
                    self.ui_sb.append(self.text_time + ', 5분에 손절 on, ' + str(self.realclose))

                # 9시 20분에는 청산
                if self.cur_time >= QTime(9, 15, 0) and self.sb_check15 == 0:
                    self.sb_check15 = 1
                    print("15분 현재가", self.realclose)
                    self.ui_sb.append(str(self.text_time) + ',' + str(self.realclose) + ',' + str(self.sb_price) + ',' + str(self.sb_num))
                    if self.ui_sb_realtrade.isChecked() == True:
                        self.send_order("send_order_rq", "0101", self.account1, 2, str(self.code), self.sb_num, 0, "03", "")
                    self.sb_num = 0


            # 장 중 반복 매매, 시작가 획득 시점부터 수행
            if self.openprice > 0 and self.cur_time < QTime(15, 30, 0) and self.cur_time > QTime(8, 55, 0):
                self.count = self.count + 1
                # 초당평균값
                self.ave5sec[self.count % 5] = self.chegang
                ave5seccg = (self.ave5sec[0] + self.ave5sec[1] + self.ave5sec[2] + self.ave5sec[3] + self.ave5sec[4]) / 5

                # 장시작 후 1번만 수행
                if self.count == 1:
                    # 장전매수주문에 대한 가격 저장
                    self.sb_price = self.openprice
                    print('장전매수주문내역')
                    self.ui_sb.append('장전매수주문내역: ' + str(self.sb_price) + ',' + str(self.sb_num))

                    # 거래량 돌파여부 확인용 초기변수
                    # self.preprice, self.prevolume, self.prepreprice = self.get_predata('233740')
                    # print('전일가:', self.preprice)
                    # print('전전일가:', self.prepreprice)
                    # self.ui_preprice.setText(str(self.preprice))
                    # print('전일거래량:', self.prevolume)
                    # self.ui_prevolume.setText(str(self.prevolume))
                    # self.ui_sb.append('시작가: ' + str(self.openprice))

                    # 잔고확인 - 향후 실거래시 잔고를 기반으로 수량 확인
                    # 장 시작 후 매수물량 반영되는 듯하니 확인필요
                    remain_num, remain_price = self.check_balance(self.account1, str(code))
                    print('잔고 업데이트:', remain_num, remain_price)
                    if remain_num == 0:
                        self.sb_num = 0

            # 장 마감 후 최종가 확인
            if self.openprice > 0 and self.cur_time > QTime(15, 31, 0) and self.endcheck == False:
                self.endcheck = True
                average3day = round((self.realclose + self.prepreprice + self.preprice) / 3)
                print('3일 평균가:', average3day)
                self.ui_v233740_average3day.setText(str(average3day))
                if self.realclose > average3day:
                    print('종가가 3일 평균가 상회하여 매수', self.realclose)
                    self.ui_sb.append(self.text_time + ', 종가매수수행, ' + str(self.realclose))
                    
        # 변수 선언
        self.common_variable()

        self.startButton.clicked.connect(lambda: self.buttonClicked('start'))
        # self.ui_orderButton.clicked.connect(lambda: self.buttonClicked('order'))
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveTrData.connect(self._ReceiveTrData)
        self.kiwoom.OnReceiveRealData.connect(self._ReceiveRealData)
        self.kiwoom.OnReceiveChejanData.connect(self._ReceiveChejanData)

        

    # 각 버튼 클릭 시 동작
    def buttonClicked(self, action):
    
        if action  == 'start':
            self.startButton.setEnabled(False)
            # 기본정보조회
            self.set_input_value("종목코드", '233740')
            nRet = self.kiwoom.dynamicCall('CommRqData(QString, QString, int, QString)', "주식기본정보", "opt10001", 0, "1001")

            # nRet = int(self.comm_rq_data("주식기본정보", "opt10001", 0, "1001"))
            if nRet == 0:
                self.ui_history_TE.append("주식 정보요청 성공")
            else:
                self.ui_history_TE.append("주식 정보요청 실패")

            # login function keyboard test
            #반복문 수행
            self.starttrading = True

    # 로그인버튼 클릭시 동작
    def _event_connect(self, err_code):
        if err_code == 0:
            self.ui_history_TE.append("login success")
            if self.kiwoom.dynamicCall('GetConnectState()') == 1:
                self.ui_history_TE.append("Connect Status: Connecting")
                self.login = True
                self.startButton.setEnabled(True)
            elif self.kiwoom.dynamicCall('GetConnectState()') == 0:
                self.ui_history_TE.append("Connect Status: 미연결")

            # 예수금 및 잔고 정보 획득
            remain_num, remain_price = self.check_balance(self.account1, '233740')
            print('233740 잔고:', remain_num, remain_price)
            print('예수금:', self.deposit)

            # 전일 종가 획득
            self.startButton.setEnabled(False)
            # 기본정보조회
            self.set_input_value("종목코드", '233740')
            nRet = self.kiwoom.dynamicCall('CommRqData(QString, QString, int, QString)', "주식기본정보", "opt10001", 0, "1001")

            # nRet = int(self.comm_rq_data("주식기본정보", "opt10001", 0, "1001"))
            if nRet == 0:
                self.ui_history_TE.append("주식 정보요청 성공")
            else:
                self.ui_history_TE.append("주식 정보요청 실패")

            #반복문 수행
            self.starttrading = True

        else:
            self.ui_history_TE.append("로그인 실패")

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
                #self.ui_openprice.setText(str(self.openprice))
            return

        elif rqname == "시가정보":
            self.openprice = self.change_format(self._get_comm_data(trcode, rqname, 0, "시가"))
            if self.openprice > 0:
                self.ui_openprice.setText(str(self.openprice))
                self.ui_history_TE.append("시작가: " + str(self.openprice))

        elif rqname == '계좌잔고':
            # multi data
            rows = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
            for i in range(rows):
                num = self._get_comm_data(trcode, rqname, i, "종목번호")
                quantity = self._get_comm_data(trcode, rqname, i, "보유수량")
                purchase_price = self._get_comm_data(trcode, rqname, i, "매입가")
                strip_num = num.lstrip('A')  # 종목번호 왼쪽의 A를 없앰
                quantity = self.change_format(quantity)
                purchase_price = self.change_format(purchase_price)

                self.opw00018_output['multi'].append([strip_num, quantity, purchase_price])

        elif rqname == 'send_order_rq':
            print('send order')

        elif rqname == '분봉차트조회':
            data_cnt = 60
            for i in range(data_cnt):  # 반복문으로 데이터를 하나씩 가져옴
                time = self._get_comm_data(trcode, rqname, i, "체결시간")
                open = self.change_format(self._get_comm_data(trcode, rqname, i, "시가"))
                high = self.change_format(self._get_comm_data(trcode, rqname, i, "고가"))
                low = self.change_format(self._get_comm_data(trcode, rqname, i, "저가"))
                close = self.change_format(self._get_comm_data(trcode, rqname, i, "현재가"))
                volume = self._get_comm_data(trcode, rqname, i, "거래량")

                self.ohlcv['time'].append(time)
                self.ohlcv['open'].append(open)
                self.ohlcv['high'].append(high)
                self.ohlcv['low'].append(low)
                self.ohlcv['close'].append(close)
                self.ohlcv['volume'].append(int(volume))

        elif rqname == '일봉차트조회':
            data_cnt = 3
            for i in range(data_cnt):  # 반복문으로 데이터를 하나씩 가져옴
                day = self._get_comm_data(trcode, rqname, i, "일자")
                open = self.change_format(self._get_comm_data(trcode, rqname, i, "시가"))
                high = self.change_format(self._get_comm_data(trcode, rqname, i, "고가"))
                low = self.change_format(self._get_comm_data(trcode, rqname, i, "저가"))
                close = self.change_format(self._get_comm_data(trcode, rqname, i, "현재가"))
                volume = self._get_comm_data(trcode, rqname, i, "거래량")

                self.ohlcv['day'].append(day)
                self.ohlcv['open'].append(open)
                self.ohlcv['high'].append(high)
                self.ohlcv['low'].append(low)
                self.ohlcv['close'].append(close)
                self.ohlcv['volume'].append(int(volume))

        elif rqname == "체결정보조회":
            data_cnt = 1
            for i in range(data_cnt):
                date = self._get_comm_data(trcode, rqname, i, "날짜")
                volume = self.change_format(self._get_comm_data(trcode, rqname, i, "거래량"))
                chegang = self._get_comm_data(trcode, rqname, i, "체결강도")

                self.chegang['date'] = date
                self.chegang['volume'] = volume
                self.chegang['chegang'] = chegang

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            print('except')
            pass

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


    # 변수 모음
    def common_variable(self):
        self.login = False
        self.starttrading = False
        self.count = 0
        self.count_60s = 0
        self.openprice = 0
        self.minprice = 1000000
        self.maxprice = 0
        self.v233740_amount = 0
        self.chegang = 100
        self.sellhoga = 0
        self.buyhoga = 10000
        self.realclose = 10000
        self.prepre_chegang = 100
        self.prev_chegang = 100
        self.now_chegang = 100
        self.real_count = 0

        self.precheck = False
        self.endcheck = False

        # 시가매매변수
        self.sb_buy = False # 장전 매수여부 확인용
        self.sb_sell = False # 손절 on 체크용

        self.sb_num = 45
        self.sb_price = 0
        self.sb_gap = 15

        self.sb_check03 = 0
        self.sb_check05 = 0
        self.sb_check15 = 0
        self.prebuyhoga = 10000

        # 장초반 흐름 파악
        self.chegangflow = [100,100,100,100,100]
        self.chegangflowcount = 0

        self.cghistory = [100,100,100,100,100]
        self.cgcount = 0
        self.cgstart = False
        self.cgend = False

        # 초당평균값
        self.ave5sec = [100,100,100,100,100]

        self.position = 0

        # 1분 봉 정보조회
        self.df_60s_1t = DataFrame(columns=("time", "count", 'volume', 'chegang'))


    # 실시간 데이터 처리
    def _ReceiveRealData(self, code, type1, data):
        if type1 == "주식체결":
            self.realclose = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 10)"))
            volume = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 15)"))
            self.sellhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 27)"))
            self.buyhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 28)"))
            self.chegang = float(self.kiwoom.dynamicCall("GetCommRealData(QString, 228)"))
            self.text_time = self.cur_time.toString("hh:mm:ss")
            self.ui_realtime.append(self.text_time + "/" + str(self.realclose) + "/" + str(self.sellhoga) + "/"+ str(self.buyhoga) + "/"+ str(volume) + "/" + str(self.chegang))

            if self.chegang < 500:
                self.real_count = self.real_count + 1
                chegangflowcount = self.real_count % 5
                self.chegangflow[chegangflowcount] = self.chegang



            if code == str(self.code) and self.openprice > 0: # 시작가 획득 후부터 동작
                # 최대 최소값 확인
                if self.realclose >= self.maxprice:
                    self.maxprice = self.realclose
                    # self.maxtime = int(self.text_time)
                    self.ui_maxprice.setText(str(self.maxprice))
                    self.ui_maxtime.setText(self.text_time)
                if self.realclose <= self.minprice:
                    self.minprice = self.realclose
                    self.ui_minprice.setText(str(self.minprice))
                    self.ui_mintime.setText(self.text_time)

                # 시가매수 결과
                if self.sb_num > 0:
                    # 수익
                    if self.buyhoga >= self.sb_price + self.sb_gap:
                        print(self.text_time, '시가매수 수익', self.buyhoga)
                        self.ui_sb.append(self.text_time + ', 시가매수 수익, ' + str(self.buyhoga) + ', ' + str(self.buyhoga - self.openprice))
                        if self.ui_sb_realtrade.isChecked() == True:
                           self.send_order("send_order_rq", "0101", self.account1, 2, str(self.code), self.sb_num, 0, "03", "")
                        self.sb_num = 0
                    # 손절
                    if self.sb_sell == True and self.buyhoga < self.sb_price - 75:
                        print(self.text_time, '시가매수 손절', self.buyhoga)
                        self.ui_sb.append(self.text_time + ', 시가매수 손절, ' + str(self.buyhoga) + ', ' + str(self.buyhoga - self.openprice))
                        if self.ui_sb_realtrade.isChecked() == True:
                            self.send_order("send_order_rq", "0101", self.account1, 2, str(self.code), self.sb_num, 0, "03", "")
                        self.sb_num = 0
                        # 손절됐을 경우 추가 매수 고려
                        # 수익률 -, 체결강도 80미만, 3,5분컷


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

    # 종목의 입력일에 대한 분봉정보 가져오기
    def get_ohlcv(self, code, thick):
        self.ohlcv = {'day': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
        self.set_input_value("종목코드", code)
        self.set_input_value("틱범위", thick)
        self.set_input_value("수정주가구분", 1)
        self.comm_rq_data("일봉차트조회", "opt10081", 0, "0101")

        df = DataFrame(self.ohlcv, columns=['day', 'open', 'high', 'low', 'close', 'volume'])

        return df
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

        if interval == 61:
            self.ui_sb.append(time + ',' + str(volume) + ',' + str(chegang))


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

    # 현재 연결상태 확인
    def get_connect_state(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

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
