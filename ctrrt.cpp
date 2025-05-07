#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <cctype>
#include <fstream>

using namespace std;

// 词法单元类型及其对应的种别码
enum TokenType
{
    // 关键字
    TOKEN_MAIN = 1,
    TOKEN_INT = 2,
    TOKEN_CHAR = 3,
    TOKEN_IF = 4,
    TOKEN_ELSE = 5,
    TOKEN_FOR = 6,
    TOKEN_WHILE = 7,
    TOKEN_RETURN = 8,
    TOKEN_VOID = 9,

    // 标识符
    TOKEN_ID = 10,

    // 双引号
    TOKEN_QUOTE_LEFT = 11,
    TOKEN_QUOTE_RIGHT = 12,

    // 常量
    TOKEN_NUM = 20,

    // 运算符和标点
    TOKEN_ASSIGN = 21,    // =
    TOKEN_PLUS = 22,      // +
    TOKEN_MINUS = 23,     // -
    TOKEN_MULTIPLY = 24,  // *
    TOKEN_DIVIDE = 25,    // /
    TOKEN_LPAREN = 26,    // (
    TOKEN_RPAREN = 27,    // )
    TOKEN_LBRACKET = 28,  // [
    TOKEN_RBRACKET = 29,  // ]
    TOKEN_LBRACE = 30,    // {
    TOKEN_RBRACE = 31,    // }
    TOKEN_COMMA = 32,     // ,
    TOKEN_COLON = 33,     // :
    TOKEN_SEMICOLON = 34, // ;
    TOKEN_GT = 35,        // >
    TOKEN_LT = 36,        // <
    TOKEN_GE = 37,        // >=
    TOKEN_LE = 38,        // <=
    TOKEN_EQ = 39,        // ==
    TOKEN_NE = 40,        // !=

    // 字符串常量
    TOKEN_STRING = 50,

    // 错误标记
    TOKEN_ERROR = 100
};

// Token结构体，存储种别码和属性值
struct Token
{
    TokenType type; // 种别码
    string lexeme;  // 词素（标记的字符表示）
    double value;   // 数值（如果是数值常量）
    int line;       // 行号
    int column;     // 列号

    // 给结构体赋予默认值
    Token(TokenType t, const string &lex, double val = 0.0, int ln = 0, int col = 0)
        : type(t), lexeme(lex), value(val), line(ln), column(col) {}
};

class LexicalAnalyzer
{
    string source;        // 源代码
    int position;         // 当前位置
    int line;             // 当前行
    int column;           // 当前列
    vector<Token> tokens; // 解析出的标记序列

    // 关键字映射表
    unordered_map<string, TokenType> keywords;

    // 初始化关键字映射表
    void initKeywords()
    {
        keywords["main"] = TOKEN_MAIN;
        keywords["int"] = TOKEN_INT;
        keywords["char"] = TOKEN_CHAR;
        keywords["if"] = TOKEN_IF;
        keywords["else"] = TOKEN_ELSE;
        keywords["for"] = TOKEN_FOR;
        keywords["while"] = TOKEN_WHILE;
        keywords["return"] = TOKEN_RETURN;
        keywords["void"] = TOKEN_VOID;
    }

    // 获取当前字符
    char currentChar()
    {
        if (position >= source.length())
            return '\0';
        return source[position];
    }

    // 获取下一个字符（不改变position）
    char peekChar()
    {
        //
        if (position + 1 >= source.length())
            return '\0';
        return source[position + 1];
    }

    // 前进一位
    void advance()
    {
        if (currentChar() != '\n')
            column++;
        else
        {
            line++;
            column = 0;
        }
        position++;
    }

    // 检查当前字符是否为指定字符，如果是则前进并返回true
    bool match(char excepted)
    {
        if (currentChar() != excepted)
            return false;
        advance();
        return true;
    }

    void skipWhitespace()
    {
        while (isspace(currentChar())) // 如果是空白数值，则跳过
            advance();
    }

    // 跳过注释
    bool skipComment()
    {
        // 单行注释
        if (currentChar() == '/' && peekChar() == '/')
        {
            advance();
            advance(); // 跳过//
            while (currentChar() != '\n' && currentChar() != '\0')
                advance();

            return true;
        }

        // 多行注释
        else if (currentChar() == '/' && peekChar() == '*')
        {
            advance();
            advance(); // 跳过/*
            while (1)
            {
                if (currentChar() == '*' && peekChar() == '/')
                {
                    advance();
                    advance(); // 跳过*/
                    break;
                }

                if (currentChar() == '\0')
                {
                    // 文件结束但注释未闭合,则报错并返回错误行
                    cout << "Error: Unclosed comment at line " << line << ", column " << column << endl;
                    return true;
                }

                advance();
            }
            return true;
        }
        return false;
    }

    // 解析标识符或关键字
    Token scanIdentifier()
    {
        int startColumn = column;
        string identifier;

        // 标识符以字母或下划线开头
        if (currentChar() == '_' || isalpha(currentChar()))
        {
            identifier += currentChar();
            advance();

            // 标识符可以包含字母、数字和下划线
            while (currentChar() == '_' || isalnum(currentChar()))
            {
                identifier += currentChar();
                advance();
            }

            // 检查是否是关键字
            if (keywords.find(identifier) != keywords.end()) // 找到了
                return Token(keywords[identifier], identifier, 0.0, line, startColumn);

            // 不是关键字，则是标识符
            return Token(TOKEN_ID, identifier, 0.0, line, startColumn);
        }

        // 错误，这个既不是标识符也不是关键字
        return Token(TOKEN_ERROR, string(1, currentChar()), 0.0, line, startColumn);
    }

    // 解析数值常量（整数、十六进制、浮点数、科学计数法）
    Token scanNumber()
    {
        int startColumn = column;
        string numStr;
        bool isHex = false;    // 是否十六进制
        bool isDouble = false; // 是否浮点数

        // 解析十六进制数字
        if (currentChar() == '0' && (peekChar() == 'x' || peekChar() == 'X')) // 如果是0x或者0X开头的认为是十六进制
        {
            isHex = 1;
            numStr += currentChar();
            numStr += peekChar();
            advance();
            advance(); // 跳过0x或者0X

            while (isxdigit(currentChar()))
            {
                numStr += currentChar();
                advance();
            }

            // 转换为整数值
            try
            {
                int value = stoi(numStr, nullptr, 16);
                return Token(TOKEN_NUM, numStr, value, line, startColumn);
            }
            catch (const exception &e) // 如果以0x开头但却不是不是十六进制的数，则报错并返回错误行
            {
                cout << "Error: Invalid hexadecimal number at line " << line << ", column " << startColumn << endl;
                return Token(TOKEN_ERROR, numStr, 0.0, line, startColumn);
            }
        }

        // 解析十进制数字
        while (isdigit(currentChar()))
        {
            numStr += currentChar();
            advance();
        }

        // 检查是否有小数点
        if (currentChar() == '.')
        {
            isDouble = true;
            numStr += currentChar();
            advance();
        }

        // 小数点后面的值
        while (isdigit(currentChar()))
        {
            numStr += currentChar();
            advance();
        }

        // 检查是否有指数
        if (currentChar() == 'e' || currentChar() == 'E')
        {
            isDouble = true;
            numStr += currentChar();
            advance();

            // 检查指数后是否含正负号（必须含正负号）
            if (currentChar() == '+' || currentChar() == '-')
            {
                numStr += currentChar();
                advance();
            }
            else
            {
                cout << "Error: Expected '+' or '-' after exponent marker at line " << line << ", column " << column << endl;
                return Token(TOKEN_ERROR, numStr, 0.0, line, startColumn);
            }

            // 如果指数后面不是数则报错
            if (!isdigit(currentChar()))
            {
                cout << "Error: Expected digit after exponent sign at line " << line << ", column " << column << endl;
                return Token(TOKEN_ERROR, numStr, 0.0, line, startColumn);
            }

            // 指数值
            while (isdigit(currentChar()))
            {
                numStr += currentChar();
                advance();
            }
        }
        // 转化为整形
        try
        {
            double value = isDouble ? stod(numStr) : stoi(numStr);
            return Token(TOKEN_NUM, numStr, value, line, startColumn);
        }
        catch (const std::exception &e)
        {
            cout << "Error: Invalid number format at line " << line << ", column " << startColumn << endl;
            return Token(TOKEN_ERROR, numStr, 0.0, line, startColumn);
        }
    }

    // 解析字符串常量
    Token scanString()
    {
        int startColumn = column;
        advance(); // 跳过开头的双引号
        string str;

        while (currentChar() != '"' && currentChar() != '\0' && currentChar() != '\n')
        {
            str += currentChar();
            advance();
        }

        if (currentChar() == '"')
        {
            advance(); // 跳过结尾的双引号
            return Token(TOKEN_STRING, str, 0.0, line, startColumn);
        }
        else
        {
            cout << "Error: Unclosed string at line " << line << ", column " << startColumn << endl;
            return Token(TOKEN_ERROR, str, 0.0, line, startColumn);
        }
    }

    Token getNextToken()
    {
        skipWhitespace();

        if (currentChar() == '\0')
            return Token(TokenType(0), "EOF", 0.0, line, column); // 文件结束

        // 跳过注释
        if (skipComment())
            return getNextToken(); // 递归调用获取下一个有效标记

        int currLine = line;
        int currColumn = column;
        char c = currentChar();

        // 标识符或关键字
        if (isalpha(c) || c == '_')
            return scanIdentifier();

        // 数值常量
        if (isdigit(c) || (c == '.' && isdigit(peekChar())))
            return scanNumber();

        // 字符串常量
        if (c == '"')
            return scanString();

        // 运算符和标点符号
        switch (c)
        {
        case '=':
            advance();
            if (currentChar() == '=')
            {
                advance();
                return Token(TOKEN_EQ, "==", 0.0, currLine, currColumn);
            }
            return Token(TOKEN_ASSIGN, "=", 0.0, currLine, currColumn);

        case '+':
            advance();
            return Token(TOKEN_PLUS, "+", 0.0, currLine, currColumn);

        case '-':
            advance();
            return Token(TOKEN_MINUS, "-", 0.0, currLine, currColumn);

        case '*':
            advance();
            return Token(TOKEN_MULTIPLY, "*", 0.0, currLine, currColumn);

        case '/':
            advance();
            return Token(TOKEN_DIVIDE, "/", 0.0, currLine, currColumn);

        case '(':
            advance();
            return Token(TOKEN_LPAREN, "(", 0.0, currLine, currColumn);

        case ')':
            advance();
            return Token(TOKEN_RPAREN, ")", 0.0, currLine, currColumn);

        case '[':
            advance();
            return Token(TOKEN_LBRACKET, "[", 0.0, currLine, currColumn);

        case ']':
            advance();
            return Token(TOKEN_RBRACKET, "]", 0.0, currLine, currColumn);

        case '{':
            advance();
            return Token(TOKEN_LBRACE, "{", 0.0, currLine, currColumn);

        case '}':
            advance();
            return Token(TOKEN_RBRACE, "}", 0.0, currLine, currColumn);

        case ',':
            advance();
            return Token(TOKEN_COMMA, ",", 0.0, currLine, currColumn);

        case ':':
            advance();
            return Token(TOKEN_COLON, ":", 0.0, currLine, currColumn);

        case ';':
            advance();
            return Token(TOKEN_SEMICOLON, ";", 0.0, currLine, currColumn);

        case '>':
            advance();
            if (currentChar() == '=')
            {
                advance();
                return Token(TOKEN_GE, ">=", 0.0, currLine, currColumn);
            }
            return Token(TOKEN_GT, ">", 0.0, currLine, currColumn);

        case '<':
            advance();
            if (currentChar() == '=')
            {
                advance();
                return Token(TOKEN_LE, "<=", 0.0, currLine, currColumn);
            }
            return Token(TOKEN_LT, "<", 0.0, currLine, currColumn);

        case '!':
            advance();
            if (currentChar() == '=')
            {
                advance();
                return Token(TOKEN_NE, "!=", 0.0, currLine, currColumn);
            }
            cout << "Error: Unexpected character '!' at line " << currLine << ", column " << currColumn << endl;
            return Token(TOKEN_ERROR, "!", 0.0, currLine, currColumn);

        default:
            cout << "Error: Unexpected character '" << c << "' at line " << currLine << ", column " << currColumn << endl;
            advance();
            return Token(TOKEN_ERROR, string(1, c), 0.0, currLine, currColumn);
        }
    }

public:
    LexicalAnalyzer() : position(0), line(1), column(0)
    {
        initKeywords();
    }

    // 从文件加载源代码
    bool loadFromFile(const string &filename)
    {
        ifstream file(filename);
        if (!file.is_open())
        {
            cout << "Error: Cannot open file " << filename << endl;
            return false;
        }

        source = string((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
        file.close();

        position = 0;
        line = 1;
        column = 0;
        tokens.clear();

        return true;
    }

    // 从字符串加载源代码
    void loadFromString(const string &str)
    {
        source = str;
        position = 0;
        line = 1;
        column = 0;
        tokens.clear();
    }

    // 执行词法分析
    vector<Token> analyze()
    {
        tokens.clear();
        position = 0;
        line = 1;
        column = 0;

        Token token = getNextToken();

        while (token.type != 0) // 不是EOF
        {
            if (token.type != TOKEN_ERROR)
                tokens.push_back(token);

            token = getNextToken();
        }
        return tokens;
    }
    void printTokens() const
    {
        for (const Token &token : tokens)
        {
            if (token.type == TOKEN_NUM)
                cout << "(" << token.type << "," << token.value << ")" << "  ";
            else
                cout << "(" << token.type << "," << token.lexeme << ")" << "  ";
        }
        cout << endl;
    }

    // 获取标记序列
    const vector<Token> &getTokens() const
    {
        return tokens;
    }
};

void testLexer(const string &sourceCode)
{
    LexicalAnalyzer lexer;
    lexer.loadFromString(sourceCode);
    lexer.analyze();
    cout << "Token序列是：";
    lexer.printTokens();
}

int main()
{
    // 测试用例1: 简单的C语言代码
    string test1 = "if x>9 x=2*x+1/3;";
    cout << "测试1：" << test1 << endl;
    testLexer(test1);

    // 测试用例2: 包含注释的代码
    string test2 = "int main() {\n"
                   "    // 这是一个注释\n"
                   "    int x = 10;\n"
                   "    /* 这是一个\n"
                   "       多行注释 */\n"
                   "    if(x > 0) {\n"
                   "        return x;\n"
                   "    }\n"
                   "    return 0;\n"
                   "}";
    cout << "\n测试2：" << endl;
    testLexer(test2);

    // 测试用例3: 包含数值常量的代码
    string test3 = "int test() {\n"
                   "    int a = 123;\n"
                   "    int b = 0x1A;\n"
                   "    double c = 3.14;\n"
                   "    double d = 2.5E+2;\n"
                   "    return 0;\n"
                   "}";
    cout << "\n测试3：" << endl;
    testLexer(test3);

    // 测试用例4: 包含字符串常量和错误的代码
    string test4 = "void print() {\n"
                   "    string msg = \"Hello, World!\";\n"
                   "    string error = \"Unclosed string;\n"
                   "    char @invalid = 'c';\n"
                   "}";
    cout << "\n测试4：" << endl;
    testLexer(test4);

    system("pause");
    return 0;
}