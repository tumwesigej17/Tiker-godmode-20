import os, threading, asyncio
from flask import Flask
import pandas as pd, numpy as np
from curl_cffi import requests as crequests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Tiker God Mode $20 LIVE"
def run_flask(): flask_app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_flask, daemon=True).start()

def fetch(ticker, rng="1y", interval="1d"):
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={rng}&interval={interval}"
    for imp in ["chrome120","safari17_0"]:
        try:
            s=crequests.Session(impersonate=imp)
            r=s.get(url, timeout=15)
            if r.status_code!=200: continue
            res=r.json()["chart"]["result"][0]
            q=res["indicators"]["quote"][0]
            df=pd.DataFrame({'Close':q['close'],'High':q['high'],'Low':q['low'],'Open':q['open'],'Volume':q['volume']})
            df.index=pd.to_datetime(res["timestamp"], unit='s')
            df=df.dropna()
            if len(df)>50: return df
        except: continue
    return pd.DataFrame()

def god_signal(ticker, mode="SWING"):
    CAPITAL=20.0
    if ticker.upper()=="NVDIA": ticker="NVDA"
    df=fetch(ticker,"5d","5m") if mode=="SCALP" else fetch(ticker,"1y","1d")
    if df.empty: df=fetch(ticker,"6mo","1d")
    if len(df)<60: return f"❌ No data {ticker}"

    price=float(df['Close'].iloc[-1])
    df['EMA9']=df['Close'].ewm(span=9).mean()
    df['EMA21']=df['Close'].ewm(span=21).mean()
    df['EMA50']=df['Close'].ewm(span=50).mean()
    df['EMA200']=df['Close'].ewm(span=200).mean()
    df['VOL20']=df['Volume'].rolling(20).mean()

    d=df['Close'].diff()
    g=d.where(d>0,0).rolling(14).mean()
    l=-d.where(d<0,0).rolling(14).mean()
    df['RSI']=100-(100/(1+g/l))

    tp=(df['High']+df['Low']+df['Close'])/3
    df['CCI']=(tp-tp.rolling(20).mean())/(0.015*(tp-tp.rolling(20).mean()).abs().rolling(20).mean())
    df['ATR']=(df['High']-df['Low']).rolling(14).mean()
    sma20=df['Close'].rolling(20).mean()
    std=df['Close'].rolling(20).std()
    df['BBW']=(sma20+2*std-(sma20-2*std))/sma20*100

    ema9=float(df['EMA9'].iloc[-1]); ema21=float(df['EMA21'].iloc[-1]); ema50=float(df['EMA50'].iloc[-1]); ema200=float(df['EMA200'].iloc[-1])
    rsi=float(df['RSI'].iloc[-1]); cci=float(df['CCI'].iloc[-1]); atr=float(df['ATR'].iloc[-1]); bbw=float(df['BBW'].iloc[-1])
    vol=float(df['Volume'].iloc[-1]); vol20=float(df['VOL20'].iloc[-1])
    vol_ok=vol>vol20*1.1

    bull = ema9>ema21>ema50 and price>ema200 and 52<rsi<70 and cci>-90 and vol_ok
    bear = ema9<ema21<ema50 and price<ema200 and 25<rsi<48 and vol_ok
    squeeze = bbw<4

    if bull and squeeze:
        sig="🟢🟢 GOD BREAKOUT + SQUEEZE - BEST TRADE"; sl=price-atr*1.3; tp1=price+atr*2.0; tp2=price+atr*3.8
    elif bull:
        sig="🟢 GOD BUY"; sl=price-atr*1.5; tp1=price+atr*1.8; tp2=price+atr*3.2
    elif bear:
        sig="🔴 GOD SELL"; sl=price+atr*1.5; tp1=price-atr*1.8; tp2=price-atr*3.2
    elif rsi<22 and cci<-150 and vol_ok:
        sig="🔵 GOD OVERSOLD SNIPER"; sl=price-atr*0.8; tp1=price+atr*2.2; tp2=price+atr*4.0
    else:
        sig=f"⚪ WAIT - Saving your $20 (BB {bbw:.1f}% Vol {'OK' if vol_ok else 'LOW'})"; sl=price-atr*1.5; tp1=price+atr*1.5; tp2=price+atr*2.5

    risk_dollars=CAPITAL*0.01
    shares=risk_dollars/abs(price-sl) if price!=sl else 0
    rr=abs(tp1-price)/abs(price-sl) if price!=sl else 0

    return f"👑 *{ticker.upper()} {mode} GOD MODE | $20* 👑\n\n💰 ${price:.2f} ATR ${atr:.2f}\nRSI {rsi:.1f} CCI {cci:.0f} BBW {bbw:.1f}%\nVol {vol/1e6:.1f}M vs {vol20/1e6:.1f}M {'✅' if vol_ok else '❌'}\n\n🚀 {sig}\n🛑 SL ${sl:.2f}\n🎯 TP1 ${tp1:.2f} (1:{rr:.1f})\n🎯 TP2 ${tp2:.2f}\n\n💵 *$20 MODE:*\nRisk ${risk_dollars:.2f} (1%)\nBuy {shares:.4f} shares (~${shares*price:.2f})\nIf lose, you still have ${CAPITAL-risk_dollars:.2f}"

async def cmd_strong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("Use: /strong NVDA"); return
    m=god_signal(context.args[0],"SWING")
    await update.message.reply_text(m, parse_mode='Markdown')

async def cmd_scalp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: await update.message.reply_text("Use: /scalp GC=F"); return
    m=god_signal(context.args[0],"SCALP")
    await update.message.reply_text(m, parse_mode='Markdown')

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 *TIKER GOD MODE $20 LIVE* 👑\nSeparate from Signal Bot\n\nCommands:\n/strong NVDA\n/strong GC=F\n/scalp BTC-USD\n\nYour $20: risk $0.20/trade only", parse_mode='Markdown')

def main():
    if not TOKEN: print("No TOKEN"); return
    try: asyncio.set_event_loop(asyncio.new_event_loop())
    except: pass
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("strong", cmd_strong))
    app.add_handler(CommandHandler("scalp", cmd_scalp))
    app.add_handler(CommandHandler("stock", cmd_strong))
    print("GOD $20 starting...")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
