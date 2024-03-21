from PyQt5 import uic
from Kiwoom_API import *
from pandas import DataFrame
import datetime
import pandas_datareader.data as web
from bs4 import BeautifulSoup
import requests

MARKET_KOSPI = 0
MARKET_KOSDAQ = 10

# UI 호출
form_class = uic.loadUiType("stock.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.today = datetime.datetime.today().strftime("%Y%m%d") # 오늘날짜 확인

        # ====== 전일 미국 증시를 참고하여 포지션 설정 ====== #
        self.check_position()

        # ====== 키움함수 불러오기 ====== #
        self.kiwoom = Kiwoom()

        # ====== 변수 선언
        self.common_variable()

        self.loginbutton.clicked.connect(lambda: self.buttonClicked('login'))
        self.startButton.clicked.connect(lambda: self.buttonClicked('start'))
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveTrData.connect(self._ReceiveTrData)
        self.kiwoom.OnReceiveRealData.connect(self._ReceiveRealData)
        self.kiwoom.OnReceiveChejanData.connect(self._ReceiveChejanData)

        # 반복함수 정의
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

    # ====== 전일 미국 증시를 참고하여 포지션 설정 ====== #
    def check_position(self):

        # Check monday
        t = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        wday = t[time.localtime().tm_wday]

        # 다우지수
        DJI = web.DataReader("^DJI", "yahoo")
        rows = len(DJI)
        today = DJI.iloc[rows - 1]['Adj Close']
        yesterday = DJI.iloc[rows - 2]['Adj Close']
        rate = ((today - yesterday) / yesterday) * 100
        daw30 = ['다우지수', today, rate]

        # NASDAQ
        IXIC = web.DataReader("^IXIC", "yahoo")
        rows = len(IXIC)
        today = IXIC.iloc[rows - 1]['Adj Close']
        yesterday = IXIC.iloc[rows - 2]['Adj Close']
        rate = ((today - yesterday) / yesterday) * 100
        ixic = ['NASDAQ', today, rate]

        # S&P 500
        GSPC = web.DataReader("^GSPC", "yahoo")
        rows = len(GSPC)
        today = GSPC.iloc[rows - 1]['Adj Close']
        yesterday = GSPC.iloc[rows - 2]['Adj Close']
        rate = ((today - yesterday) / yesterday) * 100
        gspc = ['S&P500', today, rate]

        self.ui_sb.append(str(daw30))
        self.ui_sb.append(str(ixic))
        self.ui_sb.append(str(gspc))
        self.ui_sb.append(wday)

        if wday == 'Monday' or (daw30[2] > 0 and ixic[2] > 0 and gspc[2] > 0):
            self.position = 'leverage'
            # self.code = 122630
        elif daw30[2] < 0 and ixic[2] < 0 and gspc[2] < 0:
            self.position = 'inverse'
            # self.code = 252670
        else:
            self.position = 'holding'
            # self.code = 233740

        self.ui_sb.append(str(self.position))

    # 각 버튼 클릭 시 동작
    def buttonClicked(self, action):
        if action == 'login':
            self.loginbutton.setEnabled(False)
            login = self.kiwoom.comm_connect()
            if login == 0:
                self.textEdit.append("로그인 시작")
            else:
                self.textEdit.append("로그인 실패")

    # 로그인버튼 클릭시 동작
    def _event_connect(self, err_code):
        if err_code == 0:
            self.textEdit.append("로그인 성공")
            if self.kiwoom.dynamicCall('GetConnectState()') == 1:
                self.textEdit.append("접속상태: 연결중")
                self.login = True
                self.startButton.setEnabled(True)
            elif self.kiwoom.dynamicCall('GetConnectState()') == 0:
                self.textEdit.append("접속상태: 미연결")

            # 사용자 정보 획득
            id = self.kiwoom.dynamicCall('GetLoginInfo("USER_ID")')
            self.idlabel.setText("아이디 " + id)
            name = self.kiwoom.dynamicCall('GetLoginInfo("USER_NAME")')
            self.namelabel.setText("이름 " + name)
            accounts_num = int(self.kiwoom.dynamicCall('GetLoginInfo("ACCOUNT_CNT")'))
            accounts = self.kiwoom.dynamicCall('GetLoginInfo("ACCNO")')
            accounts_list = accounts.split(';')[0:accounts_num]
            self.ui_assetnum.addItems(accounts_list)
            self.account1 = accounts_list[0]

            self.startButton.setEnabled(False)

            # 기본정보조회
            self.set_input_value("종목코드", str(122630))
            nRet = self.kiwoom.dynamicCall('CommRqData(QString, QString, int, QString)', "주식기본정보", "opt10001", 0,
                                           "1001")

            # nRet = int(self.comm_rq_data("주식기본정보", "opt10001", 0, "1001"))
            if nRet == 0:
                self.textEdit.append("주식 정보요청 성공")
            else:
                self.textEdit.append("주식 정보요청 실패")

            self.loginbutton.setEnabled(False)

            # 반복문 수행
            self.starttrading = True

        else:
            self.textEdit.append("로그인 실패")

    # TR Data 처리 함수
    def _ReceiveTrData(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if rqname == "주식기본정보":
            nCnt = int(self.kiwoom.dynamicCall('GetRepeatCnt(QString, QString)', trcode, rqname)) + 1
            for nIdx in range(0, nCnt):
                code = self._get_comm_data(trcode, rqname, nIdx, "종목코드")
                name = self._get_comm_data(trcode, rqname, nIdx, "종목명")
                volume = self._get_comm_data(trcode, rqname, nIdx, "거래량")
                open = self._get_comm_data(trcode, rqname, nIdx, "시가")
                high = self._get_comm_data(trcode, rqname, nIdx, "고가")
                low = self._get_comm_data(trcode, rqname, nIdx, "저가")
                close = self._get_comm_data(trcode, rqname, nIdx, "현재가")
                rate = self._get_comm_data(trcode, rqname, nIdx, "등락율")

                self.close = self.change_format(close)
            return

        elif rqname == "시가정보":
            self.openprice = self.change_format(self._get_comm_data(trcode, rqname, 0, "시가"))
            if self.openprice > 0:
                self.ui_openprice.setText(str(self.openprice))
                self.textEdit.append("시작가: " + str(self.openprice))

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

        elif rqname == '일별주가요청':
            data_cnt = 1
            for i in range(data_cnt):  # 반복문으로 데이터를 하나씩 가져옴
                day = self._get_comm_data(trcode, rqname, i, "날짜")
                close = self.change_format(self._get_comm_data(trcode, rqname, i, "종가"))
                ant = self.change_format2(self._get_comm_data(trcode, rqname, i, "개인"))
                corp = self.change_format(self._get_comm_data(trcode, rqname, i, "기관"))
                alien = self.change_format(self._get_comm_data(trcode, rqname, i, "외인수량"))

                self.dayinfo['day'].append(day)
                self.dayinfo['close'].append(close)
                self.dayinfo['ant'].append(ant)
                self.dayinfo['corp'].append(corp)
                self.dayinfo['alien'].append(alien)

        elif rqname == '예수금정보':
            self.deposit = self.change_format(self._get_comm_data(trcode, rqname, 0, "예수금"))

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
            self.ordernum = self.kiwoom.get_chejan_data(9203)
            print('ordernum', self.ordernum)
            self.textEdit.append("구분: 주문체결통보")
            self.textEdit.append("주문/체결시간: " + self.kiwoom.get_chejan_data(908))
            self.textEdit.append("종목명: " + self.kiwoom.get_chejan_data(302))
            self.textEdit.append("주문수량: " + self.kiwoom.get_chejan_data(900))
            self.textEdit.append("체결수량: " + self.kiwoom.get_chejan_data(911))
            self.textEdit.append("체결가격: " + self.kiwoom.get_chejan_data(910))
            self.textEdit.append("주문번호: " + self.kiwoom.get_chejan_data(9203))
            self.textEdit.append("============================")
        elif gubun == "1":
            self.textEdit.append("구분: 잔고통보")
            # self.textEdit.append("주문/체결시간: " + self.kiwoom.get_chejan_data(908))
            self.textEdit.append("종목명: " + self.kiwoom.get_chejan_data(302))
            # self.textEdit.append("체결수량: " + self.kiwoom.get_chejan_data(911))
            self.textEdit.append("종목코드: " + self.kiwoom.get_chejan_data(9001))
            self.textEdit.append("보유수량: " + self.kiwoom.get_chejan_data(930))
            self.textEdit.append("예수금: " + self.kiwoom.get_chejan_data(951))
            self.textEdit.append("============================")
            buysell = self.kiwoom.get_chejan_data(946)
            # order_num = self.get_chejan_data(9203)
            self.amount = self.kiwoom.get_chejan_data(930)
            print('잔고통보', gubun, self.amount, buysell)

        elif gubun == "3":
            self.textEdit.append("구분: 특이신호")

    # 변수 모음
    def common_variable(self):
        self.login = False
        self.starttrading = False
        self.count = 0
        self.count_60s = 0
        self.openprice = 0
        self.minprice = 1000000
        self.maxprice = 0
        self.amount = 0
        self.chegang = 100
        self.sellhoga = 0
        self.buyhoga = 10000
        self.realclose = 10000
        self.prepre_chegang = 100
        self.pre_chegang = 100
        self.now_chegang = 100
        self.real_count = 0
        self.code = 122630

        self.lsellhoga = 0
        self.lbuyhoga = 0
        self.lrealclose = 0
        self.isellhoga = 0
        self.ibuyhoga = 0
        self.irealclose = 0

        self.precheck = False
        self.endcheck = False

        # 시가매매변수
        self.sb_buy = False  # 장전 매수여부 확인용
        self.sb_sell = False  # 손절 on 체크용
        self.sb_num = self.ui_sb_num.value() ### 수정필요 - 시작 클릭 후.
        self.sb_price = 0
        self.sb_gap = 40
        self.check0903 = 0
        self.check0910 = 0

        # 개인/외인/기관
        self.pre_ant = 0; self.pre_alien = 0; self.pre_corp = 0
        self.ant = 0; self.alien = 0; self.corp = 0
        self.lgap = 80
        self.realtrade = False

        self.test1_num = 10
        self.test1_price = 0
        self.test1_benefit = 0

        self.aliencorp_num = 10
        self.aliencorp_price = 0
        self.aliencorp_benefit = 0

        self.alien_num = 10
        self.alien_price = 0
        self.alien_benefit = 0

        self.alien2_num = 10
        self.alien2_price = 0
        self.alien2_benefit = 0

        self.cgaliencorp_num = 10
        self.cgaliencorp_price = 0
        self.cgaliencorp_benefit = 0
        self.cgaliencorp_count = 0

        self.prebuyhoga = 10000

        self.cghistory = [100, 100, 100, 100, 100]
        self.cgcount = 0
        self.cgstart = False
        self.cgend = False

        # 1분 봉 정보조회
        self.df_60s_1t = DataFrame(columns=("time", "count", 'volume', 'chegang'))

    # 1초단위 반복 수행
    def timeout(self):
        self.cur_time = QTime.currentTime()
        # self.cur_time = QTime(9, 2, 10); # self.openprice = 9000 # self.today = "20200410"

        # 상태표시줄 표기
        self.show_status()

        if self.starttrading == True:

            # 전일가 획득
            if self.cur_time >= QTime(8, 40, 0) and self.precheck == False:
                self.precheck = True
                self.preprice, self.prevolume, self.prepreprice = self.get_predata(str(self.code))
                self.ui_preprice.setText(str(self.preprice))
                self.ui_prevolume.setText(str(self.prevolume))
                self.prebuyhoga = self.preprice

                print(self.position, self.code)


            # 장전매수주문
            if self.cur_time >= QTime(8, 58, 0) and self.sb_buy == False:
                self.sb_buy = True
                self.ui_sb.append('장전매수주문')
                if self.ui_sb_realtrade.isChecked() == True:
                    self.send_order("send_order_rq", "0101", self.account1, 1, str(self.code), self.sb_num, 0, "03", "")

            # 시작가 받아오기
            if self.cur_time >= QTime(9, 0, 0) and self.openprice == 0 and self.login == True:
                self.get_openprice(str(self.code))


            # 장 중 반복 매매, 시작가 획득 시점부터 수행
            if self.openprice > 0 and self.cur_time < QTime(15, 30, 0) and self.cur_time > QTime(8, 55, 0):
                self.count = self.count + 1

                # 장시작 후 1번만 수행
                if self.count == 1:

                    # 장전매수주문에 대한 가격 저장
                    self.sb_price = self.openprice
                    print('장전매수주문내역')
                    self.ui_sb.append('장전매수주문내역: ' + str(self.sb_price) + ',' + str(self.sb_num))

                    # 잔고확인 - 향후 실거래시 잔고를 기반으로 수량 확인
                    # 장 시작 후 매수물량 반영되는 듯하니 확인필요
                    remain_num, remain_price = self.check_balance(self.account1, str(self.code))
                    print('잔고 업데이트:', remain_num, remain_price)

                #================== 60초 간격 수행 ========================
                if self.count % 60 == 1:

                    # ------ 정보가공
                    # 개인, 외국인, 기관 매수
                    prepre_ant = self.pre_ant
                    prepre_alien = self.pre_alien
                    prepre_corp = self.pre_corp

                    self.pre_ant = self.ant
                    self.pre_alien = self.alien
                    self.pre_corp = self.corp

                    kospi, kosdaq, kospi200 = self.check_aliencorp()
                    self.ant = kospi[0]
                    self.alien = kospi[1]
                    self.corp = kospi[2]

                    # AVERAGE
                    avg3alien = 0
                    if prepre_ant != 0 and prepre_alien != 0 and prepre_corp != 0:
                        avg3ant = (prepre_ant + self.pre_ant + self.ant)/3
                        avg3alien = (prepre_alien + self.pre_alien + self.alien)/3
                        avg3corp = (prepre_corp + self.pre_corp + self.corp)/3

                    # Leverage 체결강도 기록
                    self.prepre_chegang = self.pre_chegang
                    self.pre_chegang = self.now_chegang
                    self.now_chegang = self.lchegang

                    # 정보출력
                    self.ui_info.append(
                        str(self.text_time) + ', ' + str(self.lsellhoga) + ', ' + str(
                            self.now_chegang) + ', ' + str(self.ant) + ', ' + str(self.alien) + ', ' + str(self.corp))

                    # ----- 매매기법
                   # 외인/기관이 모두 +이면 매수 - onetime
                    if self.aliencorp_price == 0 and self.alien > 0 and self.corp > 0 and (self.pre_alien <= 0 or self.pre_corp <= 0):
                        self.aliencorp_price = self.lsellhoga
                        self.ui_sb.append(
                            self.text_time + ', 외인/기관 +전환, ' + str(self.lsellhoga) + ', ' + str(
                                self.alien) + ', ' + str(self.corp))

                    # 시가보다 낮을경우
                    # 시가가 전일가보다 5프로 이상하락
                    # 외인 +이면 매수 - onetime
                    if self.alien_price == 0 and self.alien > 0 and self.pre_alien <= 0 and self.cur_time > QTime(9, 5, 0):
                        self.alien_price = self.lsellhoga
                        self.ui_sb.append(
                            self.text_time + ', 외인만 +전환, ' + str(self.lsellhoga) + ', ' + str(
                                self.alien))

                    # 외인 +이면 매수2 - onetime
                    if self.cur_time > QTime(9, 5, 0) and self.alien2_price == 0 and self.alien > 0 and self.pre_alien <= 0:
                        self.alien2_price = self.lsellhoga
                        self.ui_sb.append(
                            self.text_time + ', 외인만 +전환2, ' + str(self.lsellhoga) + ', ' + str(
                                self.alien))

                    # 외인2 매도
                    if self.alien2_price > 0 and self.alien < avg3alien:
                        print('외인 -로 전환2', self.alien, self.pre_alien, avg3alien)
                        self.alien2_benefit += self.lbuyhoga - self.alien_price
                        self.ui_sb.append(
                            self.text_time + ', 외인만 +전환2,3평이하시매도 ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.alien2_price))
                        self.alien2_price = 0

                    # 체강,외인,기관 전환 매수
                    #  시가매수이후적용
                    # 외인-50이상필수조전
                    # 체강100이상?, 체강,외인이 직직전부터상승
                    # 시가처리가 30분이상 걸리면? 시가처리보다먼저무조건이걸리면?
                    # 예상시가가 전일가보다 1.5프로 이상이면 시가매수안함?
                    # 2회차부터 전일가대비 5프로이상시 보류
                    # 첫회가 10시반전?
                    # 외인기관이 모두 -일경우는 무시?
                    # 1번 fail하면 매수중지?
                    if self.cur_time > QTime(9, 10, 0) and self.cur_time < QTime(14, 0, 0) and self.prepre_chegang < self.pre_chegang and prepre_alien < self.pre_alien and self.cgaliencorp_price == 0 and self.pre_chegang < self.chegang and self.pre_alien < self.alien and self.pre_corp < self.corp:

                        self.cgaliencorp_price = self.lsellhoga
                        if self.ui_alien_realtrade.isChecked() == True and self.sb_num == 0 and self.cgaliencorp_count == 0 and (self.realclose > self.openprice or self.alien > -50 or self.corp > -50) and self.alien > -100:
                            self.cgaliencorp_count = self.cgaliencorp_count + 1
                            self.realtrade = True
                            self.send_order("send_order_rq", "0101", self.account1, 1, str(self.code), self.cgaliencorp_num, 0, "03", "")
                        self.ui_sb.append(
                            self.text_time + ', 체강/외인/기관 전환, ' + str(self.lsellhoga) + ', ' + str(self.chegang) + ', ' + str(
                                self.alien) + ', ' + str(self.corp))



                if self.cur_time > QTime(9, 3, 0) and self.check0903 == 0:
                    self.check0903 = 1
                    if self.test1_price == 0 and self.alien > 0 and self.corp > 0:
                        print('buy alien, corp > 0')
                        self.test1_price = self.lsellhoga
                        self.ui_sb.append(
                            self.text_time + ', alien, corp > 0 test1, ' + str(self.lsellhoga) + ', ' + str(self.alien) + ', ' + str(self.corp))

                # 9:10 check start
                if self.cur_time > QTime(9, 10, 0) and self.check0910 == 0:
                    self.check0910 = 1
                    self.sb_sell = True
                    self.ui_sb.append(self.text_time + ', 9시10분')


    # 실시간 데이터 처리
    def _ReceiveRealData(self, code, type1, data):
        # print(code, type1)
        if type1 == "주식체결" and code == "122630":
            self.lrealclose = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 10)"))
            lvolume = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 15)"))
            self.lsellhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 27)"))
            self.lbuyhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 28)"))
            self.lchegang = float(self.kiwoom.dynamicCall("GetCommRealData(QString, 228)"))
            self.text_time = self.cur_time.toString("hh:mm:ss")
            self.ui_RTleverage.append(self.text_time + "/" + str(self.lrealclose) + "/" + str(self.lsellhoga) + "/" + str(
                self.lbuyhoga) + "/" + str(lvolume) + "/" + str(self.lchegang))

            if self.openprice > 0:  # 시작가 획득 후부터 동작
                # 최대 최소값 확인
                if self.lrealclose >= self.maxprice:
                    self.maxprice = self.lrealclose
                    # self.maxtime = int(self.text_time)
                    self.ui_lmax.setText(str(self.maxprice))
                    self.ui_lmaxt.setText(self.text_time)
                if self.lrealclose <= self.minprice:
                    self.minprice = self.lrealclose
                    self.ui_lmin.setText(str(self.minprice))
                    self.ui_lmint.setText(self.text_time)

                if self.test1_price > 0:
                    if self.lbuyhoga >= self.test1_price + self.sb_gap:
                        self.test1_benefit += self.lbuyhoga - self.test1_price
                        print(self.text_time, 'alien, corp > 0 success!', self.lbuyhoga)
                        self.ui_sb.append(
                            self.text_time + ', alien, corp > 0 success!, ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.test1_price) + ', ' + str(self.test1_benefit))
                        self.test1_price = 0

                    if self.lbuyhoga < self.test1_price - self.lgap:
                        self.test1_benefit += self.lbuyhoga - self.test1_price
                        print(self.text_time, 'alien, corp > 0 failed...,', self.lbuyhoga)
                        self.ui_sb.append(
                            self.text_time + ', alien, corp > 0 failed..., ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.test1_price) + ', ' + str(self.test1_benefit))
                        self.test1_price = 0

                if self.aliencorp_price > 0:
                    if self.lbuyhoga >= self.aliencorp_price + self.lgap:
                        self.aliencorp_benefit += self.lbuyhoga - self.aliencorp_price
                        print(self.text_time, '외인/기관 전환 success!', self.lbuyhoga)
                        self.ui_sb.append(
                            self.text_time + ', 외인/기관 전환 success!, ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.aliencorp_price) + ', ' + str(self.aliencorp_benefit))
                        self.aliencorp_price = 0

                    if self.lbuyhoga < self.aliencorp_price - self.lgap:
                        self.aliencorp_benefit += self.lbuyhoga - self.aliencorp_price
                        print(self.text_time, '외인/기관 전환 failed...,', self.lbuyhoga)
                        self.ui_sb.append(
                            self.text_time + ', 외인/기관 전환 failed..., ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.aliencorp_price) + ', ' + str(self.aliencorp_benefit))
                        self.aliencorp_price = 0

                if self.alien_price > 0:
                    if self.lbuyhoga >= self.alien_price + 80:
                        print(self.text_time, '외인 전환 success!', self.lbuyhoga)
                        self.alien_benefit += self.lbuyhoga - self.alien_price
                        self.ui_sb.append(
                            self.text_time + ', 외인 전환 success!, ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.alien_price) + ', ' + str(self.alien_benefit))
                        self.alien_price = 0

                    if self.lbuyhoga < self.alien_price - 80:
                        print(self.text_time, '외인 전환 failed...,', self.lbuyhoga)
                        self.alien_benefit += self.lbuyhoga - self.alien_price
                        self.ui_sb.append(
                            self.text_time + ', 외인 전환 failed..., ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.alien_price) + ', ' + str(self.alien_benefit))
                        self.alien_price = 0

                if self.cgaliencorp_price > 0:
                    if self.lbuyhoga > self.cgaliencorp_price + 55:
                        self.cgaliencorp_benefit += self.lbuyhoga - self.cgaliencorp_price
                        if self.ui_alien_realtrade.isChecked() == True and self.realtrade == True:
                            self.send_order("send_order_rq", "0101", self.account1, 2, str(self.code), self.cgaliencorp_num, 0, "03", "")
                            self.realtrade = False
                        print(self.text_time, '체강/외인/기관 전환 success!', self.lbuyhoga)
                        self.ui_sb.append(
                            self.text_time + ', 체강/외인/기관 전환 success!, ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.cgaliencorp_price) + ', ' + str(self.cgaliencorp_benefit))
                        self.cgaliencorp_price = 0

                    if self.lbuyhoga < self.cgaliencorp_price - 55:
                        self.cgaliencorp_benefit += self.lbuyhoga - self.cgaliencorp_price
                        if self.ui_alien_realtrade.isChecked() == True and self.realtrade == True:
                            self.send_order("send_order_rq", "0101", self.account1, 2, str(self.code), self.cgaliencorp_num, 0, "03", "")
                            self.realtrade = False
                        print(self.text_time, '체강/외인/기관 전환 failed...,', self.lbuyhoga)
                        self.ui_sb.append(
                            self.text_time + ', 체강/외인/기관 전환 failed..., ' + str(self.lbuyhoga) + ', ' + str(
                                self.lbuyhoga - self.cgaliencorp_price) + ', ' + str(self.cgaliencorp_benefit))
                        self.cgaliencorp_price = 0


        if type1 == "주식체결" and code == "252670":
            self.irealclose = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 10)"))
            ivolume = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 15)"))
            self.isellhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 27)"))
            self.ibuyhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 28)"))
            self.ichegang = float(self.kiwoom.dynamicCall("GetCommRealData(QString, 228)"))
            self.text_time = self.cur_time.toString("hh:mm:ss")

            if self.openprice > 0:  # 시작가 획득 후부터 동작
                # 최대 최소값 확인
                if self.irealclose >= self.maxprice:
                    self.maxprice = self.irealclose
                    # self.maxtime = int(self.text_time)
                    # self.ui_imax.setText(str(self.maxprice))
                    # self.ui_imaxt.setText(self.text_time)
                if self.irealclose <= self.minprice:
                    self.minprice = self.irealclose
                    # self.ui_imin.setText(str(self.minprice))
                    # self.ui_imint.setText(self.text_time)

        code = self.code
        if type1 == "주식체결":
            self.realclose = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 10)"))
            volume = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 15)"))
            self.sellhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 27)"))
            self.buyhoga = self.change_format(self.kiwoom.dynamicCall("GetCommRealData(QString, 28)"))
            self.chegang = float(self.kiwoom.dynamicCall("GetCommRealData(QString, 228)"))
            self.text_time = self.cur_time.toString("hh:mm:ss")

            if code == self.code and self.openprice > 0:  # 시작가 획득 후부터 동작

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
                    if self.sb_sell == True and self.buyhoga < self.sb_price - (self.sb_gap * 4):
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

    # tr 입력값을 서버 통신 전에 입력
    def set_input_value(self, id, value):
        self.kiwoom.dynamicCall('SetInputValue(QString, QString)', id, value)

    # tr을 서버에 전송한다.
    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.kiwoom.dynamicCall('CommRqData(QString, QString, int, QString)', rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()
        return

    def _get_comm_data(self, trcode, rqname, index, item_name):
        ret = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item_name)
        return ret.strip()

    def show_status(self):
        self.text_time = self.cur_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + self.text_time
        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"
        self.statusbar.showMessage(state_msg + " | " + time_msg)

    # def code_changed(self):
    #    code = self.ui_orderItemCode.text()
    #    name = self.kiwoom.get_master_code_name(code)
    #    self.ui_orderItemName.setText(name)

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

    # 종목의 입력일에 대한 일별주가요청
    def get_dayinfo(self, code, date):
        self.dayinfo = {'day': [], 'close': [], 'ant': [], 'corp': [], 'alien': []}
        self.set_input_value("종목코드", code)
        self.set_input_value("조회일자", date)
        self.set_input_value("표시구분", 0)

        self.comm_rq_data("일별주가요청", "opt10086", 0, "0101")

        df = DataFrame(self.dayinfo, columns=['day', 'close', 'ant', 'corp', 'alien'])

        return df


    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-+0')
        if strip_data == '':
            strip_data = '0'
        return int(strip_data)

    @staticmethod
    def change_format2(data):
        if data[:1] == '-':
            strip_data = data[1:]
        else:
            strip_data = data
        return int(strip_data)

    # 개인/외국인/기관 매매동향
    def check_aliencorp(self):
        BaseUrl = 'https://finance.naver.com/'

        r = requests.get(BaseUrl)
        soup = BeautifulSoup(r.text, 'lxml')
        items = soup.find_all('dl', {'class': 'dl'})
        count = 0
        for item in items:
            dd = item.text.split()
            if count == 0:

                kospi = int(dd[1].replace(',', '').lstrip('+')), int(dd[4].replace(',', '').lstrip('+')), int(
                    dd[7].replace(',', '').lstrip('+'))
            elif count == 1:
                kosdaq = int(dd[1].replace(',', '').lstrip('+')), int(dd[4].replace(',', '').lstrip('+')), int(
                    dd[7].replace(',', '').lstrip('+'))
            elif count == 2:
                kospi200 = int(dd[1].replace(',', '').lstrip('+')), int(dd[4].replace(',', '').lstrip('+')), int(
                    dd[7].replace(',', '').lstrip('+'))
            count = count + 1

        return kospi, kosdaq, kospi200


    # ====================== 키움 Open API =======================

    # 시가정보
    def get_openprice(self, code):
        self.set_input_value("종목코드", code)
        self.comm_rq_data("시가정보", "opt10001", 0, "1001")
        return

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}
        return

    # 계좌 잔고 정보
    def check_balance(self, account, code):
        remain_num, remain_price = 0, 0
        self.reset_opw00018_output()  # 저장할 배열을 초기화
        self.set_input_value("계좌번호", account)
        self.comm_rq_data("계좌잔고", "opw00018", 0, "2000")

        item_count = len(self.opw00018_output['multi'])
        for j in range(item_count):
            row = self.opw00018_output['multi'][j]
            if row[0] == code:
                remain_num = int(row[1])
                remain_price = int(row[2])
        # 예수금 정보
        self.set_input_value("계좌번호", account)
        self.comm_rq_data("예수금정보", "opw00001", 0, "2000")

        return remain_num, remain_price

    def get_info(self, df_code_s, code, count, thick):
        now = datetime.datetime.now()  # 함수 수행 시간
        time = now.strftime('%H%M%S')

        chegangdata = self.get_chegang(code)
        volume = chegangdata['volume']
        chegang = self.chegangdata['chegang']

        df_code_s.loc[count] = [time, count, volume, chegang]

        return 1

    def get_chegang(self, code):
        self.chegang = {'code': [], 'date': [], 'volume': [], 'chegang': []}
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

    # 매수 주문
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        lRet = self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                       [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
        if lRet == 0:
            self.textEdit.append("주문이 전송 되었습니다.")
        else:
            self.textEdit.append("주문이 전송 실패 하였습니다.")
        return lRet


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
        # self.login_event_loop = QEventLoop()
        # self.login_event_loop.exec_()
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()