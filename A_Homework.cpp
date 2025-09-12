#include<bits/stdc++.h>
using namespace std;

int main(){
    int t;
    cin>>t;
    while(t--){
        int n;
        cin >> n;
        string s;
        cin >> s;
        int m;
        cin>>m;
        string p;
        cin>>p;
        string temp,f="",b="";
        cin>>temp;
        int i=0;
        for(char c : temp){
            if(c=='V')f+=p[i++];
            else b+=p[i++];
        }
        reverse(f.begin(),f.end());
        cout<<f+s+b<<endl;
    }
    return 0;
}               