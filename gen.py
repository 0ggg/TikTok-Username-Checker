import itertools

def gen():
    charset = 'abcdefghijklmnopqrstuvwxyz0123456789'
    with open('users.txt', 'w', encoding='utf-8') as f:
        for combo in itertools.product(charset, repeat=4):
            f.write(''.join(combo) + '\n')

    total = len(charset) ** 4
    print(f"Done Gen {total} Usernames")

if __name__ == "__main__":
    gen()
