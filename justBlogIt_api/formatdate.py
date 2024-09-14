from datetime import datetime

class FormatDate:
    @staticmethod
    def format_date(date):
        if date.year == datetime.now().year:
            if date.month == datetime.now().month:
                if date.day == datetime.now().day:
                    if date.hour == datetime.now().hour:
                        if date.minute == datetime.now().minute:
                            if date.second == datetime.now().second:
                                return "now"
                            else:
                                if datetime.now().second - date.second < 59:
                                    return "now"
                                return "{} secs ago".format(datetime.now().second - date.second)
                        else:
                            if datetime.now().minute - date.minute == 1:
                                return "1 min ago"
                            return "{} mins ago".format(datetime.now().minute - date.minute)
                    else:
                        if datetime.now().hour - date.hour == 1:
                            print(datetime.now().hour - date.hour)
                            return "1 hr ago"
                        return "{} hrs ago".format(datetime.now().hour - date.hour)

                else:
                    if datetime.now().day - date.day == 1:
                        print("this is the day", datetime.now().day - date.day)
                        return "1 day ago"
                    print("this is the day", datetime.now().day - date.day)
                    return "{} days ago".format(datetime.now().day - date.day)
            else:
                if datetime.now().month - date.month == 1:
                    return "1 mon ago"
                return "{} mons ago".format(datetime.now().year - date.year)
        else:
            if datetime.now().year - date.year == 1:
                return "1 yr ago"
            return "{} yrs ago".format(datetime.now().year - date.year) 

