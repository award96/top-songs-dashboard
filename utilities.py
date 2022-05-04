import pandas as pd


def create_date_list(start, end):
    """
    ARGS:
        start - string, a date represented by a string in the format 'YYYY-MM-DD'
        end - string, a date represented by a string in the format 'YYYY-MM-DD'

    RETURNS:
        list - a list of strings that represent dates via the format 'YYYY-MM-DD'
    """
    date_range = pd.date_range(start, end).to_pydatetime().tolist()
 
    return [d.strftime('%Y-%m-%d') for d in date_range]

if __name__ == "__main__":
    print(create_date_list('2022-04-29', '2022-05-04'))
