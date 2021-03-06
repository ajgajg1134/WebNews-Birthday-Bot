#!/usr/bin/env python
from CSHLDAP import CSHLDAP
from datetime import date, datetime
from csh_webnews import Webnews
import argparse

def checkBirthday(ldap):
    today = date.today()
    for member in allMembersWithBirthdaysOnDate(ldap, today):
        name = member["displayName"]
        if len(name) < 1:
            continue
        displayName = name[0]

def allMembersWithBirthdays(ldap):
    """
    Finds all active members in LDAP and strips those without B-Days
    Returns: The list of all active members with a birthday
    """
    activeMembers = ldap.search(active="1")
    members = []
    for memberTuple in activeMembers:
        if len(memberTuple) < 1:
            continue
        member = memberTuple[1]
        birthday = birthdateFromMember(member)
        if not birthday:
            continue
        members.append(member)
    return members

def allMembersWithBirthdaysOnDate(ldap, day):
    """
    Finds all members with a birthday on a specified date.
    Returns: An array of members whos birthday falls on day
    """
    allMembers = allMembersWithBirthdays(ldap)
    birthdayMembers = []
    for member in allMembers:
        birthday = birthdateFromMember(member)
        if day.month != birthday.month or day.day != birthday.day:
            continue
        birthdayMembers.append(member)
    return birthdayMembers

def birthdateFromMember(member):
    """
    Takes a member and returns their birthday in a date form.
    Returns: A date object or a None if the member doesn't have a birthday
    """
    if not "birthday" in member:
        return None
    birthday = member["birthday"]
    if len(birthday) < 1:
        return None
    birthdayString = birthday[0]
    memberMonthDay = birthdayString[:8]
    birthdate = datetime.strptime(memberMonthDay, "%Y%m%d")
    return date(year=birthdate.year, month=birthdate.month, day=birthdate.day)

def message(ldap):
    """
    Finds all active members whos birthday is today, parses a subject and body for WebNews
    Returns: The subject line, The body
    """
    day = date.today()
    birthdays = allMembersWithBirthdaysOnDate(ldap, day)
    numberOfBirthdays = len(birthdays)
    if numberOfBirthdays == 0:
        return None, None
    plural = "s" if numberOfBirthdays > 1 else ""
    name = "Today" if numberOfBirthdays > 1 else birthdays[0]["cn"]
    subject = name[0] + "'s Birthday" + plural
    string = ""
    for member in birthdays:
        birthdate = birthdateFromMember(member)
        age = date.today().year - birthdate.year
        name = member["displayName"]
        commonName = member["cn"]
        if len(name) < 1:
            continue
        nameString = name[0]
        memberString = nameString + " is " + str(age) + " years old.\n"
        string += memberString
    string += "\nShower on sight!\n\n(This post was automatically generated by the WebNews Birthday Bot.)"
    return subject, string

def main(user=None, password=None, apiKey=None, test=False):
    ldap = CSHLDAP(user, password)
    subject, post = message(ldap)
    if not post:
        print("No birthdays today.")
        return
    newsgroup = "csh.test" if test else "csh.noise"
    webnews = Webnews(api_key=apiKey, api_agent="WebNews Birthday Bot")
    webnews.compose(newsgroup=newsgroup, subject=subject, body=post)
    print(post)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Find users with a birthday.')
    parser.add_argument("user", help="Specify a username.")
    parser.add_argument("password", help="Specify the password for the user.")
    parser.add_argument("apikey", help="API key for posting to WebNews")
    parser.add_argument("--test", "-t",
                        action="store_true",
                        help="Posts to csh.test instead of csh.noise")
    args = parser.parse_args()

    if not args.apikey:
        print("No API key provided.")
        exit()

    main(user=args.user, password=args.password,
         apiKey=args.apikey, test=args.test)
